"""BRIEF A queue 6: capture.from_image (D-020, CONTRACTS) — label photo -> normalize, [] if unreadable."""
import random
import struct
import subprocess
import zlib

import pytest

from core import capture
from core.contracts import Drug

# Synthetic pharmacy label (I1): made-up patient, Rx number and pharmacy.
LABEL = """SYNTHETIC PHARMACY  555-0100
Rx# 0000123   ALEX SAMPLE
CLOPIDOGREL 75 MG TABLET
Generic for: PLAVIX
TAKE 1 TABLET BY MOUTH ONCE DAILY
QTY: 30   REFILLS: 2"""


@pytest.fixture(autouse=True)
def _no_real_ocr(monkeypatch):
    """Tests never depend on a tesseract install or a local vision model; the tesseract and VLM tests
    fake them explicitly."""
    from core import local_llm
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


def _chunk(ctype: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body))


def _png_with(*chunks: bytes) -> bytes:
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    return capture._PNG_SIG + ihdr + b"".join(chunks) + idat + _chunk(b"IEND", b"")


def _jpeg_with_comment(comment: bytes) -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    com = b"\xff\xfe" + struct.pack(">H", len(comment) + 2) + comment
    return b"\xff\xd8" + app0 + com + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00" + b"\x00" * 16 + b"\xff\xd9"


def test_contract_signature_returns_drugs():
    out = capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png")
    assert out == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert all(isinstance(d, Drug) for d in out)


def test_full_label_gives_one_clopidogrel_75():
    assert capture.from_image(capture.demo_png(LABEL), "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]


def test_ibuprofen_label_for_offline_beat():
    out = capture.from_image(capture.demo_png("IBUPROFEN 200 MG TABLETS\nPain reliever/fever reducer (NSAID)"), "image/png")
    assert out == [Drug(ingredient="ibuprofen", dose_mg=200)]


def test_combination_label_splits():
    out = capture.from_image(capture.demo_png("ZESTORETIC 20/12.5 MG TAB"), "image/png")
    assert [d.ingredient for d in out] == ["lisinopril", "hydrochlorothiazide"]
    assert [d.dose_mg for d in out] == [20, 12.5]


def test_png_text_and_ztxt_chunks():
    t = _png_with(_chunk(b"tEXt", capture.LABEL_KEY + b"\x00omeprazole 20 mg"))
    z = _png_with(_chunk(b"zTXt", capture.LABEL_KEY + b"\x00\x00" + zlib.compress(b"simvastatin 40 mg")))
    assert capture.from_image(t, "image/png") == [Drug(ingredient="omeprazole", dose_mg=20)]
    assert capture.from_image(z, "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]


def test_compressed_itxt_chunk():
    body = capture.LABEL_KEY + b"\x00\x01\x00en\x00\x00" + zlib.compress("Prinivil 10 mg".encode())
    assert capture.from_image(_png_with(_chunk(b"iTXt", body)), "image/png") == [Drug(ingredient="lisinopril", dose_mg=10)]


def test_other_png_text_keywords_are_ignored():
    png = _png_with(_chunk(b"tEXt", b"Description\x00clopidogrel 75 mg"))
    assert capture.from_image(png, "image/png") == []


def test_jpeg_comment():
    jpg = _jpeg_with_comment(capture.LABEL_KEY + b": Ecotrin 81 mg")
    assert capture.from_image(jpg, "image/jpeg") == [Drug(ingredient="aspirin", dose_mg=81)]


def test_jpeg_without_label_comment_is_unreadable():
    assert capture.from_image(_jpeg_with_comment(b"made with a camera"), "image/jpeg") == []


def test_sniff_trusts_bytes_not_mime():
    png = capture.demo_png("Plavix 75 mg")
    assert capture.from_image(png, "image/jpeg") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert capture.sniff(b"GIF89a" + b"\x00" * 10) == "gif"
    assert capture.sniff(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"


@pytest.mark.parametrize("data,mime", [
    (b"", "image/png"),
    (b"not an image at all, just text", "image/png"),
    (capture.demo_png("Plavix 75 mg"), "application/pdf"),
    (capture.demo_png("Plavix 75 mg"), ""),
    (capture.demo_png("Plavix 75 mg")[:40], "image/png"),     # truncated
    (None, "image/png"),
])
def test_unreadable_gives_empty(data, mime):
    assert capture.from_image(data, mime) == []


def test_unknown_or_misspelled_drug_gives_empty():
    assert capture.from_image(capture.demo_png("WIDGETOL 10 MG"), "image/png") == []
    assert capture.from_image(capture.demo_png("Clopidogrl 75 mg"), "image/png") == []   # no fuzzy guess (I4)


def test_oversized_upload_refused(monkeypatch):
    monkeypatch.setattr(capture, "MAX_BYTES", 100)
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == []


def test_ocr_off(monkeypatch):
    monkeypatch.setenv("GV_OCR", "off")
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == []


def test_never_raises_on_random_bytes():
    rng = random.Random(7)
    base = capture.demo_png(LABEL)
    for _ in range(300):
        b = bytearray(base)
        for _ in range(rng.randint(1, 8)):
            b[rng.randrange(8, len(b))] = rng.randrange(256)
        out = capture.from_image(bytes(b[: rng.randint(8, len(b))]), "image/png")
        assert isinstance(out, list)
    for _ in range(100):
        junk = b"\xff\xd8\xff" + bytes(rng.randrange(256) for _ in range(rng.randint(0, 200)))
        assert isinstance(capture.from_image(junk, "image/jpeg"), list)


def test_typed_fallback():
    assert capture.from_text("Plavix 75 mg") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert capture.from_text("") == []
    assert capture.from_text(None) == []


class _FakeRun:
    def __init__(self, stdout=b"", returncode=0, exc=None):
        self.stdout, self.returncode, self.exc, self.calls = stdout, returncode, exc, []

    def __call__(self, args, **kw):
        self.calls.append((args, kw))
        if self.exc:
            raise self.exc
        return subprocess.CompletedProcess(args, self.returncode, stdout=self.stdout, stderr=b"")


def test_tesseract_used_when_no_embedded_text(monkeypatch):
    fake = _FakeRun(stdout=b"SIMVASTATIN 40 MG\nTAKE AT BEDTIME\n")
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/local/bin/tesseract")
    monkeypatch.setattr(capture.subprocess, "run", fake)
    plain = _png_with()
    assert capture.from_image(plain, "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]
    (args, kw), = fake.calls
    assert args == ["/usr/local/bin/tesseract", "stdin", "stdout"]
    assert kw["input"] == plain and kw["timeout"] == capture.OCR_TIMEOUT_S


def test_embedded_text_wins_over_tesseract_in_auto(monkeypatch):
    fake = _FakeRun(stdout=b"IBUPROFEN 200 MG")
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/bin/tesseract")
    monkeypatch.setattr(capture.subprocess, "run", fake)
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert fake.calls == []


def test_mode_tesseract_skips_embedded(monkeypatch):
    fake = _FakeRun(stdout=b"IBUPROFEN 200 MG")
    monkeypatch.setenv("GV_OCR", "tesseract")
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/bin/tesseract")
    monkeypatch.setattr(capture.subprocess, "run", fake)
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == [Drug(ingredient="ibuprofen", dose_mg=200)]


def test_mode_embedded_never_runs_tesseract(monkeypatch):
    fake = _FakeRun(stdout=b"IBUPROFEN 200 MG")
    monkeypatch.setenv("GV_OCR", "embedded")
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/bin/tesseract")
    monkeypatch.setattr(capture.subprocess, "run", fake)
    assert capture.from_image(_png_with(), "image/png") == []
    assert fake.calls == []


@pytest.mark.parametrize("fake", [
    _FakeRun(exc=subprocess.TimeoutExpired("tesseract", 30)),
    _FakeRun(exc=OSError("broken")),
    _FakeRun(stdout=b"CLOPIDOGREL 75 MG", returncode=1),
])
def test_tesseract_failure_gives_empty(monkeypatch, fake):
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/bin/tesseract")
    monkeypatch.setattr(capture.subprocess, "run", fake)
    assert capture.from_image(_png_with(), "image/png") == []


def test_no_tesseract_and_no_embedded_text_gives_empty():
    assert capture.from_image(_png_with(), "image/png") == []


def test_capture_does_no_network_io():
    """I2: capture never does network I/O itself and never reaches the cloud; the only model it may
    call is the localhost-only `local_llm` (D-029)."""
    src = open(capture.__file__).read()
    assert "from . import local_llm" in src
    for mod in ("httpx", "requests", "socket", "urllib", "aiohttp", "http.client", "cloud"):
        assert f"import {mod}" not in src and f"from {mod}" not in src and f".{mod} import" not in src
