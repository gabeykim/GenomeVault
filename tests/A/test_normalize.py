"""A queue 2: normalize.to_ingredients maps brand/generic text to ingredients (F2, M3)."""
import json
import pathlib

import pytest

from core.contracts import Drug
from core.normalize import NAMES_PATH, to_ingredients


def _pairs(text):
    return [(d.ingredient, d.dose_mg) for d in to_ingredients(text)]


def test_brand_to_ingredient():
    assert to_ingredients("Plavix") == [Drug(ingredient="clopidogrel")]


def test_generic_is_recognized_and_lowercased():
    assert _pairs("Clopidogrel") == [("clopidogrel", None)]


@pytest.mark.parametrize("text", ["", "   ", "Xyzzol 10 mg", "plavx", "take with food"])
def test_unknown_returns_empty(text):
    assert to_ingredients(text) == []


@pytest.mark.parametrize("text,expected", [
    ("Plavix 75 mg", [("clopidogrel", 75)]),
    ("plavix 75mg", [("clopidogrel", 75)]),
    ("aspirin 81", [("aspirin", 81)]),
    ("Clopidogrel bisulfate 75 mg tablets", [("clopidogrel", 75)]),
    ("Advil 200 mg, take 2 tablets", [("ibuprofen", 200)]),
    ("aspirin 2 tablets", [("aspirin", None)]),
    ("aspirin 0.081 g", [("aspirin", 81)]),
])
def test_dose_parsing(text, expected):
    assert _pairs(text) == expected


def test_combination_pill_split_with_strengths():
    assert _pairs("Zestoretic 10/12.5 mg") == [("lisinopril", 10), ("hydrochlorothiazide", 12.5)]
    assert _pairs("Vytorin 10/40") == [("ezetimibe", 10), ("simvastatin", 40)]


def test_combination_without_matching_strengths_has_no_dose():
    assert _pairs("Vytorin 40 mg") == [("ezetimibe", None), ("simvastatin", None)]


def test_hyphenated_generic_combo():
    assert [d.ingredient for d in to_ingredients("lisinopril-hydrochlorothiazide")] == [
        "lisinopril", "hydrochlorothiazide"]


def test_multiword_names_and_otc_label():
    assert [d.ingredient for d in to_ingredients("Motrin IB")] == ["ibuprofen"]
    assert [d.ingredient for d in to_ingredients("Prilosec OTC 20 mg")] == ["omeprazole"]
    assert [d.ingredient for d in to_ingredients("Klor-Con")] == ["potassium chloride"]


def test_several_drugs_in_one_text_each_get_own_dose():
    assert _pairs("aspirin 81 mg and Plavix 75 mg") == [("aspirin", 81), ("clopidogrel", 75)]


def test_duplicate_ingredient_listed_once():
    assert _pairs("Plavix (clopidogrel) 75 mg") == [("clopidogrel", 75)]


def test_alex_meds_and_demo_drugs_all_resolve():
    for name, ing in [("Plavix", "clopidogrel"), ("Prilosec", "omeprazole"), ("Zocor", "simvastatin"),
                      ("Zestril", "lisinopril"), ("Ecotrin", "aspirin"), ("Advil", "ibuprofen"),
                      ("Protonix", "pantoprazole")]:
        assert [d.ingredient for d in to_ingredients(name)] == [ing], name


def test_names_file_schema():
    data = json.loads(pathlib.Path(NAMES_PATH).read_text())
    assert data["version"] and data["source"]
    for name, ings in data["names"].items():
        assert name == name.lower() and name.strip() == name
        assert ings and all(i == i.lower() for i in ings)
