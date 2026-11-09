"""Names for every drug the router can ask about (PLAN F2, M3; I4).

A drug in B's bucket universe that `normalize` cannot read never reaches the router: typing
"Celexa" would give `[]`. These tests keep the name table in step with the universe, and check that
adding names added no flags.
"""
import json
import pathlib
import re

import pytest

from core import normalize, rules
from core.contracts import Drug, Profile

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# Drugs D's eval questions name (eval/queries.json Q03, Q05, Q16) and the bucket universe v5 drugs.
EVAL_DRUGS = ["codeine", "citalopram", "warfarin", "st_johns_wort"]


def _alex() -> Profile:
    return Profile.model_validate_json((DATA / "alex_profile.json").read_text())


def _latest_buckets() -> pathlib.Path | None:
    files = sorted((DATA / "buckets").glob("v*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    return files[-1] if files else None


def _universe_drugs(path: pathlib.Path) -> set[str]:
    d = json.loads(path.read_text())
    keys = [k for b in d["buckets"] for k in b["keys"]] + list(d.get("aliases", {}))
    drugs = set()
    for k in keys:
        for part in k.split("|"):
            if ":" in part or "<" in part or ">" in part:   # gene:phenotype or lab band
                continue
            drugs.add(part)
    return drugs


def _ingredients(text: str) -> list[str]:
    return [d.ingredient for d in normalize.to_ingredients(text)]


@pytest.mark.parametrize("drug", EVAL_DRUGS)
def test_eval_drugs_normalize_to_themselves(drug):
    assert _ingredients(drug.replace("_", " ")) == [drug]


def test_every_bucket_universe_drug_is_readable():
    path = _latest_buckets()
    if path is None:
        pytest.skip("no data/buckets/v*.json on this branch yet (B's partition)")
    missing = sorted(d for d in _universe_drugs(path) if _ingredients(d.replace("_", " ")) != [d])
    assert not missing, f"{path.name}: normalize can't read {missing}"


@pytest.mark.parametrize("text,expected", [
    ("Celexa 20 mg", [("citalopram", 20.0)]),
    ("St. John's Wort 300 mg", [("st_johns_wort", 300.0)]),
    ("st johns wort", [("st_johns_wort", None)]),
    ("Hypericum extract", [("st_johns_wort", None)]),
    ("Tylenol with Codeine 300/30 mg", [("acetaminophen", 300.0), ("codeine", 30.0)]),
    ("Bactrim DS 800/160 mg", [("sulfamethoxazole", 800.0), ("trimethoprim", 160.0)]),
    ("Isosorbide mononitrate 30 mg", [("isosorbide", 30.0)]),
    ("Depakote 500 mg", [("valproate", 500.0)]),
    ("Lexapro 10mg", [("escitalopram", 10.0)]),
    ("Coumadin 5 mg", [("warfarin", 5.0)]),
])
def test_brands_and_synonyms(text, expected):
    assert [(d.ingredient, d.dose_mg) for d in normalize.to_ingredients(text)] == expected


def test_tylenol_alone_is_still_just_acetaminophen():
    assert _ingredients("Tylenol 500 mg") == ["acetaminophen"]


@pytest.mark.parametrize("drug", ["codeine", "citalopram", "st_johns_wort", "meloxicam", "piroxicam"])
def test_new_names_add_no_flags_for_alex(drug):
    # Names only: no rule covers these, so Alex gets no flag and every pair stays no_data (I4).
    # Meloxicam and piroxicam are NSAIDs but not listed class members, so no X5-style flag.
    p = _alex()
    assert rules.check(Drug(ingredient=drug), p) == []
    assert rules.no_data_keys(Drug(ingredient=drug), p)


def test_codeine_key_stays_no_data():
    # D-021: CYP2D6 is not assessed, so no rule may use it.
    assert rules.key_state("CYP2D6:not_assessed|codeine") == "no_data"
