"""capture.label_drugs: one label is one product (F2, M3, S2; I4). Drug names in a label's warnings
are not drugs the user takes, so they must not reach rules.check (a Plavix label alone must not fire
X5). All label text is synthetic (I1)."""
import pytest

from core import capture
from core.contracts import Drug


@pytest.fixture(autouse=True)
def _no_real_ocr(monkeypatch):
    from core import local_llm
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


PLAVIX_WITH_WARNING = """SYNTHETIC PHARMACY  555-0100
Rx# 0000123   ALEX SAMPLE
CLOPIDOGREL 75 MG TABLET
Generic for: PLAVIX
TAKE 1 TABLET BY MOUTH ONCE DAILY
Do not take aspirin or other NSAIDs such as ibuprofen (Advil) unless your doctor tells you to."""

ADVIL_DRUG_FACTS = """Advil Ibuprofen Tablets 200 mg
Pain reliever/fever reducer (NSAID)
Warnings: Ask a doctor before use if you are taking aspirin for heart attack or stroke, or a blood
thinner such as warfarin."""


def _img(text):
    return capture.from_image(capture.demo_png(text), "image/png")


def test_plavix_label_warning_names_are_dropped():
    assert _img(PLAVIX_WITH_WARNING) == [Drug(ingredient="clopidogrel", dose_mg=75)]


def test_otc_drug_facts_warning_names_are_dropped():
    assert _img(ADVIL_DRUG_FACTS) == [Drug(ingredient="ibuprofen", dose_mg=200)]


def test_plavix_photo_does_not_fire_x5():
    from core import rules
    from core.graph import load_profile
    profile = load_profile()
    flags = [f for d in _img(PLAVIX_WITH_WARNING) for f in rules.check(d, profile)]
    assert all(f.id != "X5" for f in flags)
    assert not any("ibuprofen" in f.key or "warfarin" in f.key for f in flags)


def test_warning_in_same_line_as_product_is_dropped():
    assert _img("CLOPIDOGREL 75 MG. Avoid aspirin and ibuprofen.") == [Drug(ingredient="clopidogrel", dose_mg=75)]


def test_strength_from_later_line_with_same_ingredient():
    text = "PLAVIX\nclopidogrel bisulfate 75 mg\nDo not take with omeprazole."
    assert _img(text) == [Drug(ingredient="clopidogrel", dose_mg=75)]


def test_strength_from_later_warning_with_other_drug_is_not_used():
    text = "ADVIL\nPain reliever\nIf you take aspirin 81 mg daily, ask a doctor."
    assert _img(text) == [Drug(ingredient="ibuprofen")]


def test_name_and_strength_split_across_lines():
    out = _img("LISINOPRIL-HCTZ\n20-12.5 MG TAB")
    assert [d.ingredient for d in out] == ["lisinopril", "hydrochlorothiazide"]


def test_combination_pill_on_one_line_stays_whole():
    out = _img("ZESTORETIC 20/12.5 MG TAB\nDo not take with ibuprofen.")
    assert [(d.ingredient, d.dose_mg) for d in out] == [("lisinopril", 20), ("hydrochlorothiazide", 12.5)]


def test_decimal_strength_is_not_cut_as_a_sentence():
    assert capture.label_drugs("hydrochlorothiazide 12.5 mg") == [Drug(ingredient="hydrochlorothiazide", dose_mg=12.5)]


def test_no_drug_name_gives_empty():
    assert capture.label_drugs("SYNTHETIC PHARMACY\nTake 1 tablet daily.") == []
    assert capture.label_drugs("") == []


def test_typed_text_keeps_every_name():
    assert {d.ingredient for d in capture.from_text("clopidogrel and aspirin")} == {"clopidogrel", "aspirin"}


def test_tesseract_text_uses_the_one_product_rule(monkeypatch):
    monkeypatch.setenv("GV_OCR", "tesseract")
    monkeypatch.setattr(capture, "tesseract_text", lambda data: PLAVIX_WITH_WARNING)
    plain = capture.demo_png("")
    assert capture.from_image(plain, "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
