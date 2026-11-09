"""Allergy engine (PLAN F3 "allergy", M4; I4 exact keys, I6 curated, I7 never reassure).

Alex's record lists a penicillin allergy (P5). Before this engine nothing produced an `allergy`
Flag, although the contract allows the engine and F3 is a Must.
"""
import json
import pathlib

import pytest

from core import normalize, rules
from core.contracts import Drug, Profile

ROOT = pathlib.Path(__file__).resolve().parents[2]
RULES = ROOT / "data" / "rules"
VOCAB = {i.lower() for ings in json.loads((RULES / "drug_names.json").read_text())["names"].values() for i in ings}


def _alex() -> Profile:
    return Profile.model_validate_json((ROOT / "data" / "alex_profile.json").read_text())


def _with(allergies, meds=()) -> Profile:
    return Profile(genotypes={}, phenotypes={}, meds=[Drug(ingredient=m) for m in meds],
                   conditions=[], allergies=list(allergies), labs=[])


def _allergy_flags(drug, profile):
    return [f for f in rules.check(Drug(ingredient=drug), profile) if f.engine == "allergy"]


# --- tables ------------------------------------------------------------------------------------

def test_groups_list_only_readable_members():
    t = rules.tables()["allergy"]
    for g in t["groups"].values():
        assert set(g["members"]) <= VOCAB          # every member can be typed or photographed
    for r in t["rules"]:
        assert r["group"] in t["groups"]


def test_allergy_keys_are_known():
    for k in ("allergy:penicillin|amoxicillin", "allergy:sulfonamide_antibiotic|sulfamethoxazole",
              "allergy:amoxicillin|amoxicillin"):
        assert k in rules.all_keys() and rules.key_state(k) == "known"


@pytest.mark.parametrize("key", ["allergy:penicillin|cephalexin", "allergy:penicillin|ceftriaxone",
                                 "allergy:sulfonamide_antibiotic|furosemide", "allergy:amoxicillin|ampicillin",
                                 "allergy:sulfonamide_antibiotic|trimethoprim"])
def test_no_cross_group_inference(key):
    # I4: no cephalosporin cross-reactivity, no non-antibiotic sulfonamides, no member-to-member.
    assert key not in rules.all_keys() and rules.key_state(key) == "no_data"


# --- Alex --------------------------------------------------------------------------------------

def test_alex_amoxicillin_flags_penicillin_allergy():
    flags = _allergy_flags("amoxicillin", _alex())
    assert len(flags) == 1
    f = flags[0]
    assert f.key == "allergy:penicillin|amoxicillin" and f.id == "AL-001"
    assert f.severity == "high" and not f.needs_cloud
    assert f.evidence == ["allergy on record: penicillin", "amoxicillin is a penicillin"]


@pytest.mark.parametrize("label,drug", [("Augmentin 875/125 mg", "amoxicillin"), ("Pen VK 500 mg", "penicillin_v"),
                                        ("Zosyn", "piperacillin"), ("Amoxil 500 mg", "amoxicillin")])
def test_alex_label_reaches_allergy_flag(label, drug):
    keys = {f.key for d in normalize.to_ingredients(label) for f in rules.check(d, _alex())}
    assert f"allergy:penicillin|{drug}" in keys


def test_alex_discharge_flags_unchanged():
    # The allergy engine adds nothing to the X1-X5 demo: no penicillin on Alex's med list.
    assert not [f for f in rules.check_all(_alex()) if f.engine == "allergy"]
    assert {f.id for f in rules.check_all(_alex())} <= {"X1", "X2", "X3", "X4", "X5"}


@pytest.mark.parametrize("drug", ["clavulanate", "tazobactam", "cephalexin", "trimethoprim", "clopidogrel"])
def test_alex_non_members_get_no_allergy_flag(drug):
    assert _allergy_flags(drug, _alex()) == []


# --- matching ----------------------------------------------------------------------------------

@pytest.mark.parametrize("written", ["Penicillin", " penicillins ", "PCN", "penicillin allergy"])
def test_group_aliases_match(written):
    flags = _allergy_flags("ampicillin", _with([written]))
    assert [f.key for f in flags] == ["allergy:penicillin|ampicillin"]
    assert flags[0].evidence[0] == f"allergy on record: {written.strip()}"


@pytest.mark.parametrize("written", ["sulfa", "Sulfa drugs", "sulfonamides", "sulfonamide antibiotic"])
def test_sulfa_matches_sulfamethoxazole_not_trimethoprim(written):
    p = _with([written])
    by = {d.ingredient: _allergy_flags(d.ingredient, p) for d in normalize.to_ingredients("Bactrim DS 800/160 mg")}
    assert [f.key for f in by["sulfamethoxazole"]] == ["allergy:sulfonamide_antibiotic|sulfamethoxazole"]
    assert by["trimethoprim"] == []


def test_member_allergy_matches_only_itself():
    p = _with(["amoxicillin"])
    assert [f.key for f in _allergy_flags("amoxicillin", p)] == ["allergy:amoxicillin|amoxicillin"]
    assert _allergy_flags("ampicillin", p) == []     # I4: no member-to-member inference


def test_underscore_member_written_as_words():
    assert [f.key for f in _allergy_flags("penicillin_v", _with(["Penicillin V"]))] == ["allergy:penicillin_v|penicillin_v"]


@pytest.mark.parametrize("allergies", [[], ["latex"], ["peanuts"], ["cephalosporins"], ["penicilin"]])
def test_unlisted_or_misspelled_allergy_gives_no_flag(allergies):
    # No fuzzy matching: an allergy that is not an authored group, alias or member stays unflagged.
    assert _allergy_flags("amoxicillin", _with(allergies)) == []


def test_group_match_wins_over_member_match():
    p = _with(["penicillin", "amoxicillin"])
    assert [f.key for f in _allergy_flags("amoxicillin", p)] == ["allergy:penicillin|amoxicillin"]


def test_allergy_text_never_reassures():
    for r in rules.tables()["allergy"]["rules"]:
        low = r["text"].lower()
        assert "safe" not in low and "fine" not in low and "okay" not in low
