"""BRIEF A queue 8: an unlisted pair gives no flags plus a `no_data` marker (PLAN I4, P6 answer states)."""
import pathlib

from core import rules
from core.contracts import Drug, Profile, pair_key

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _alex() -> Profile:
    return Profile.model_validate_json((DATA / "alex_profile.json").read_text())


def test_every_table_key_is_known():
    for k in rules.all_keys() | rules.expected_keys():
        assert rules.key_state(k) == "known", k


def test_pantoprazole_is_no_data_not_extrapolated_from_omeprazole():
    # S6: clopidogrel|omeprazole is curated; clopidogrel|pantoprazole is deliberately absent (P5).
    assert rules.key_state("clopidogrel|omeprazole") == "known"
    assert rules.key_state("clopidogrel|pantoprazole") == "no_data"
    p = _alex()
    flags = rules.check(Drug(ingredient="pantoprazole", dose_mg=40), p)
    assert all("pantoprazole" not in f.key for f in flags)
    assert "clopidogrel|pantoprazole" in rules.no_data_keys(Drug(ingredient="pantoprazole"), p)


def test_unknown_drug_gives_no_flags_and_every_pair_no_data():
    p = _alex()
    drug = Drug(ingredient="Zzzfakeamine")
    assert rules.check(drug, p) == []
    others = sorted({m.ingredient for m in p.meds})
    assert rules.no_data_keys(drug, p) == sorted(pair_key("zzzfakeamine", o) for o in others)


def test_no_data_keys_never_include_a_flagged_or_expected_pair():
    p = _alex()
    for med in p.meds + [Drug(ingredient="ibuprofen", dose_mg=400)]:
        flagged = {f.key for f in rules.check(med, p)}
        marked = set(rules.no_data_keys(med, p))
        assert not marked & flagged, med.ingredient
        assert not marked & rules.expected_keys(), med.ingredient


def test_omeprazole_marks_only_its_unlisted_pairs():
    p = _alex()
    marked = rules.no_data_keys(Drug(ingredient="omeprazole"), p)
    assert "clopidogrel|omeprazole" not in marked
    assert "aspirin|omeprazole" in marked
    assert len(marked) == len(set(marked))


def test_not_assessed_gene_keys_are_no_data():
    assert rules.key_state("CYP2D6:poor_metabolizer|codeine") == "no_data"
    assert rules.key_state("CYP2D6:not_assessed|clopidogrel") == "no_data"


def test_none_listed_not_returned_without_curated_entry():
    states = {rules.key_state(k) for k in ["a|b", "clopidogrel|pantoprazole", "simvastatin|alt>120"]}
    assert states == {"no_data"}
