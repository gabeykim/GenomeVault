"""C's shared label set (C-022, to-A 1526): capture.from_image on `phone/samples/*.png` with the texts in
`phone/samples/labels.json`. One set is used by A's tests and C's phone samples (Dhiaa's 15:20 item 2).

Two layers:
- The label texts, copied here from C's labels.json at 80bf651, run on every branch through the PNG iTXt
  path and a faked OCR path. They are synthetic (I1).
- The real files in `phone/samples/` (C owns them) run when that folder exists, i.e. on main after C's PR
  merges. Each PNG must give exactly the right Drug, both from its embedded `gv:label` text and, with
  the iTXt chunk stripped, from OCR text, and the Drug must flag like the typed med (F2, F3, M3, S2).
No real tesseract or vision model is needed.
"""
import json
from pathlib import Path

import pytest

from core import capture, local_llm, rules
from core.contracts import Drug

from .test_alex_flags import _alex
from .test_capture_g3_labels import _strip_text

SAMPLES = Path(__file__).resolve().parents[2] / "phone" / "samples"

# file -> (label text as in labels.json, expected Drug, Alex's flag ids)
EXPECT = {
    "aspirin.png": ("ASPIRIN 81 MG TABLET\nLow-dose aspirin\nTAKE 1 TABLET BY MOUTH DAILY",
                    Drug(ingredient="aspirin", dose_mg=81), []),
    "clopidogrel.png": ("CLOPIDOGREL 75 MG TABLET\nGeneric for: PLAVIX\nTake 1 tablet by mouth daily",
                        Drug(ingredient="clopidogrel", dose_mg=75), ["X1", "X2"]),
    "omeprazole.png": ("OMEPRAZOLE 20 MG CAPSULE\nGeneric for: PRILOSEC\n"
                       "TAKE 1 CAPSULE BY MOUTH DAILY BEFORE BREAKFAST",
                       Drug(ingredient="omeprazole", dose_mg=20), ["X2"]),
    "simvastatin.png": ("SIMVASTATIN 40 MG TABLET\nGeneric for: ZOCOR\nTAKE 1 TABLET BY MOUTH AT BEDTIME",
                        Drug(ingredient="simvastatin", dose_mg=40), ["X3"]),
    "lisinopril.png": ("LISINOPRIL 10 MG TABLET\nGeneric for: ZESTRIL\nTAKE 1 TABLET BY MOUTH DAILY",
                       Drug(ingredient="lisinopril", dose_mg=10), ["X4"]),
    "amoxicillin.png": ("AMOXICILLIN 500 MG CAPSULE\nGeneric for: AMOXIL\n"
                        "TAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY\n"
                        "Do not take if you are allergic to penicillin.",
                        Drug(ingredient="amoxicillin", dose_mg=500), ["AL-001"]),
    "ibuprofen.png": ("IBUPROFEN 200 MG TABLET\nPain reliever / fever reducer",
                      Drug(ingredient="ibuprofen", dose_mg=200), ["X5"] * 4),   # one X5 per med pair
}

needs_samples = pytest.mark.skipif(not (SAMPLES / "labels.json").exists(),
                                   reason="phone/samples/ lands with C's PR (C-022)")


@pytest.fixture(autouse=True)
def _local_only(monkeypatch):
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


def _flags(drug):
    return sorted(f.id for f in rules.check(drug, _alex()))


@pytest.mark.parametrize("name", EXPECT)
def test_label_text_gives_exactly_the_right_drug_and_flags(monkeypatch, name):
    text, want, flags = EXPECT[name]
    assert capture.from_image(capture.demo_png(text), "image/png") == [want]
    monkeypatch.setattr(capture, "tesseract_text", lambda data: text)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == [want]
    assert _flags(want) == flags


def test_penicillin_warning_is_not_a_product():
    """The Amoxil label's allergy line names penicillin; only amoxicillin is the product (A-013)."""
    text = EXPECT["amoxicillin.png"][0]
    assert [d.ingredient for d in capture.label_drugs(text)] == ["amoxicillin"]


@needs_samples
def test_shared_set_is_the_set_a_tests():
    texts = json.loads((SAMPLES / "labels.json").read_text())
    assert set(texts) == set(EXPECT)
    for name, text in texts.items():
        assert (SAMPLES / name).exists(), name
        want = EXPECT[name][1]
        assert capture.label_drugs(text) == [want], name


@needs_samples
@pytest.mark.parametrize("name", EXPECT)
def test_sample_png_gives_exactly_the_right_drug(name):
    want, flags = EXPECT[name][1], EXPECT[name][2]
    got = capture.from_image((SAMPLES / name).read_bytes(), "image/png")
    assert got == [want]
    assert _flags(got[0]) == flags


@needs_samples
@pytest.mark.parametrize("name", EXPECT)
def test_sample_png_without_embedded_text_reads_through_ocr(monkeypatch, name):
    """A VLM/OCR-only check (C's note): strip `gv:label`, then the reader sees only pixels. OCR is faked
    with labels.json's text, so this pins the parse, not the engine."""
    texts = json.loads((SAMPLES / "labels.json").read_text())
    bare = _strip_text((SAMPLES / name).read_bytes())
    assert capture.embedded_text(bare, "png") == ""
    assert capture.from_image(bare, "image/png") == []          # no engine, no guess (I4)
    monkeypatch.setattr(capture, "tesseract_text", lambda data: texts[name])
    assert capture.from_image(bare, "image/png") == [EXPECT[name][1]]
