"""normalize: combination strengths written "10-40 mg" or "20/12.5 mg" go to the ingredients in order
(F2, M3, M4). A wrong low dose would silence a dose-conditioned flag (X3 is simvastatin >20 mg), so a
strength that doesn't line up is unknown (`None`, which rules treat as "worth asking"), never a guess.
All label text is synthetic (I1)."""
import pytest

from core import capture, rules
from core.contracts import Drug
from core.graph import load_profile
from core.normalize import to_ingredients


def _doses(text):
    return [(d.ingredient, d.dose_mg) for d in to_ingredients(text)]


@pytest.mark.parametrize("text, expected", [
    ("ezetimibe-simvastatin 10-40 mg", [("ezetimibe", 10), ("simvastatin", 40)]),
    ("amlodipine-atorvastatin 5-40 mg", [("amlodipine", 5), ("atorvastatin", 40)]),
    ("LISINOPRIL-HCTZ 20-12.5 MG TAB", [("lisinopril", 20), ("hydrochlorothiazide", 12.5)]),
    ("lisinopril / hctz 20/12.5 mg", [("lisinopril", 20), ("hydrochlorothiazide", 12.5)]),
    ("amoxicillin-clavulanate 875-125 mg", [("amoxicillin", 875), ("clavulanate", 125)]),
    ("AMOX-CLAV 875-125 MG TAB", [("amoxicillin", 875), ("clavulanate", 125)]),
    ("Zestoretic 20/12.5 mg", [("lisinopril", 20), ("hydrochlorothiazide", 12.5)]),
    ("Vytorin 10/40", [("ezetimibe", 10), ("simvastatin", 40)]),
])
def test_combination_strengths_follow_ingredient_order(text, expected):
    assert _doses(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("ezetimibe-simvastatin 40 mg", [("ezetimibe", None), ("simvastatin", None)]),   # one number, two drugs
    ("simvastatin 20-40 mg", [("simvastatin", None)]),                               # a range
])
def test_strengths_that_dont_line_up_are_unknown(text, expected):
    assert _doses(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("clopidogrel 75 mg and aspirin 81 mg", [("clopidogrel", 75), ("aspirin", 81)]),
    ("simvastatin 40 mg - take at bedtime", [("simvastatin", 40)]),
    ("aspirin 2 tablets", [("aspirin", None)]),
    ("Plavix 75mg", [("clopidogrel", 75)]),
])
def test_single_products_unchanged(text, expected):
    assert _doses(text) == expected


def _no_simvastatin_on_file():
    p = load_profile()
    return p.model_copy(update={"meds": [m for m in p.meds if m.ingredient != "simvastatin"]})


@pytest.mark.parametrize("label", ["ezetimibe-simvastatin 10-40 mg tablet", "simvastatin 20-40 mg"])
def test_combo_or_range_label_still_fires_x3(label):
    """Before: "10-40 mg" read as simvastatin 10 mg, and X3 (>20 mg) stayed silent."""
    profile = _no_simvastatin_on_file()
    ids = {f.id for d in to_ingredients(label) for f in rules.check(d, profile)}
    assert "X3" in ids


AMOXIL_LABEL = """SYNTHETIC PHARMACY  555-0100
Rx# 0000456   ALEX SAMPLE
AMOXICILLIN 500 MG CAPSULE
Generic for: AMOXIL
TAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY FOR 10 DAYS
Do not take if you are allergic to penicillin. Finish all medication unless otherwise directed."""


@pytest.fixture
def _no_real_ocr(monkeypatch):
    from core import local_llm
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


def test_amoxil_label_photo_gives_al001(_no_real_ocr):
    drugs = capture.from_image(capture.demo_png(AMOXIL_LABEL), "image/png")
    assert drugs == [Drug(ingredient="amoxicillin", dose_mg=500)]
    flags = [f for d in drugs for f in rules.check(d, load_profile())]
    assert [(f.id, f.key) for f in flags] == [("AL-001", "allergy:penicillin|amoxicillin")]


def test_augmentin_label_strengths(_no_real_ocr):
    drugs = capture.from_image(capture.demo_png("AMOXICILLIN-CLAV 875-125 MG TABLET\nGeneric for: AUGMENTIN"),
                               "image/png")
    assert [(d.ingredient, d.dose_mg) for d in drugs] == [("amoxicillin", 875), ("clavulanate", 125)]
