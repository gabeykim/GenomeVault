"""D-029: label photo -> local vision model -> exact-key normalize (F2, M3, I2, I4).

The model is faked: these tests never need Ollama. They check that the model only reads, that every
name still goes through the exact-key table, and that anything odd falls back instead of guessing."""
import base64
import json
import struct
import zlib

import pytest

from core import capture, local_llm
from core.contracts import Drug

def _plain_png() -> bytes:
    """A synthetic PNG with no embedded label text, so the VLM is the first source that reads."""
    def chunk(ctype: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body))
    return (capture._PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b""))


class FakeVLM:
    def __init__(self, reply=None, exc=None):
        self.reply, self.exc, self.calls = reply, exc, []

    def __call__(self, prompt, system="", images=None, format=None, model=None):
        self.calls.append({"prompt": prompt, "images": images, "format": format, "model": model})
        if self.exc:
            raise self.exc
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "qwen2.5vl:7b", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


def _fake(monkeypatch, **kw) -> FakeVLM:
    fake = FakeVLM(**kw)
    monkeypatch.setattr(local_llm, "generate", fake)
    return fake


def test_plavix_label_read_by_vlm(monkeypatch):
    fake = _fake(monkeypatch, reply={"brand_name": "Plavix", "ingredient": "clopidogrel bisulfate", "strength_mg": 75})
    img = _plain_png()
    assert capture.from_image(img, "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    (call,) = fake.calls
    assert call["model"] == "qwen2.5vl:7b" and call["format"] == "json"
    assert call["images"] == [base64.b64encode(img).decode("ascii")]
    assert "do not guess" in call["prompt"].lower()


def test_brand_only_and_ingredient_only(monkeypatch):
    _fake(monkeypatch, reply={"brand_name": "Zocor", "ingredient": None, "strength_mg": "40 mg"})
    assert capture.from_image(_plain_png(), "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]
    _fake(monkeypatch, reply={"brand_name": None, "ingredient": "IBUPROFEN", "strength_mg": 200})
    assert capture.from_image(_plain_png(), "image/png") == [Drug(ingredient="ibuprofen", dose_mg=200)]


def test_combination_strength_splits_like_typed_text(monkeypatch):
    _fake(monkeypatch, reply={"brand_name": "Zestoretic", "ingredient": "lisinopril", "strength_mg": "20/12.5"})
    assert capture.from_image(_plain_png(), "image/png") == capture.from_text("Zestoretic 20/12.5 mg")
    assert {d.ingredient for d in capture.from_text("Zestoretic")} == {"lisinopril", "hydrochlorothiazide"}


def test_unknown_or_misspelled_name_gives_empty_never_a_guess(monkeypatch):
    for reply in ({"brand_name": "Plavlx", "ingredient": None, "strength_mg": 75},
                  {"brand_name": "Foozol", "ingredient": "foozolamide", "strength_mg": 10}):
        _fake(monkeypatch, reply=reply)
        assert capture.from_image(_plain_png(), "image/png") == []


def test_brand_and_ingredient_disagree_gives_empty(monkeypatch):
    _fake(monkeypatch, reply={"brand_name": "Plavix", "ingredient": "simvastatin", "strength_mg": 75})
    assert capture.from_image(_plain_png(), "image/png") == []


def test_vlm_read_stops_auto_mode_before_tesseract(monkeypatch):
    _fake(monkeypatch, reply={"brand_name": "Foozol", "ingredient": None, "strength_mg": None})
    ran = []
    monkeypatch.setattr(capture, "tesseract_text", lambda data: ran.append(1) or "IBUPROFEN 200 MG")
    assert capture.from_image(_plain_png(), "image/png") == []
    assert ran == []


@pytest.mark.parametrize("kw", [
    {"exc": ConnectionError("ollama not running")},
    {"exc": TypeError("old local_llm without images=")},
    {"reply": "not json"},
    {"reply": "[1, 2]"},
    {"reply": {"brand_name": None, "ingredient": "", "strength_mg": 75}},
    {"reply": {"brand_name": 42, "ingredient": ["clopidogrel"]}},
])
def test_unavailable_or_bad_answer_falls_through_to_tesseract(monkeypatch, kw):
    _fake(monkeypatch, **kw)
    monkeypatch.setattr(capture, "tesseract_text", lambda data: "SIMVASTATIN 40 MG")
    assert capture.from_image(_plain_png(), "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]


def test_unconfigured_model_is_never_called(monkeypatch):
    fake = _fake(monkeypatch, reply={"brand_name": "Plavix"})
    for value in ("", "set-me"):
        monkeypatch.setattr(local_llm, "VLM_MODEL", value)
        assert capture.from_image(_plain_png(), "image/png") == []
    monkeypatch.delattr(local_llm, "VLM_MODEL")             # main's local_llm before PLAN v1.3
    assert capture.from_image(_plain_png(), "image/png") == []
    assert fake.calls == []


def test_embedded_text_wins_and_vlm_not_called(monkeypatch):
    fake = _fake(monkeypatch, reply={"brand_name": "Zocor", "strength_mg": 40})
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert fake.calls == []


def test_modes(monkeypatch):
    fake = _fake(monkeypatch, reply={"brand_name": "Zocor", "ingredient": None, "strength_mg": 40})
    monkeypatch.setenv("GV_OCR", "vlm")                      # skips embedded text
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]
    for mode in ("embedded", "tesseract", "off"):
        monkeypatch.setenv("GV_OCR", mode)
        capture.from_image(_plain_png(), "image/png")
    assert len(fake.calls) == 1


def test_vlm_mode_with_model_down_gives_empty(monkeypatch):
    _fake(monkeypatch, exc=ConnectionError("down"))
    monkeypatch.setenv("GV_OCR", "vlm")
    monkeypatch.setattr(capture, "tesseract_text", lambda data: "SIMVASTATIN 40 MG")
    assert capture.from_image(_plain_png(), "image/png") == []


def test_non_images_never_reach_the_model(monkeypatch):
    fake = _fake(monkeypatch, reply={"brand_name": "Plavix"})
    assert capture.from_image(b"%PDF-1.7 Plavix 75 mg label", "image/png") == []
    assert capture.from_image(_plain_png(), "application/pdf") == []
    assert fake.calls == []


@pytest.mark.parametrize("strength, dose", [
    (75, 75), (75.0, 75), ("75", 75), ("75 mg", 75), ("75mg", 75), ("0.5 g", 500),
    (None, None), (True, None), (-5, None), (0, None), ("seventy-five", None), ("75; rm -rf", None),
])
def test_strength_is_only_ever_a_plain_number(strength, dose):
    assert capture.drugs_from_fields("Plavix", "", strength) == [Drug(ingredient="clopidogrel", dose_mg=dose)]


def test_alex_gets_no_extra_flags_from_a_vlm_read(monkeypatch):
    """A VLM read of one of Alex's own meds gives the same Drug as the typed name (F3 unchanged)."""
    _fake(monkeypatch, reply={"brand_name": "Plavix", "ingredient": "clopidogrel", "strength_mg": 75})
    assert capture.from_image(_plain_png(), "image/png") == capture.from_text("Plavix 75 mg")
