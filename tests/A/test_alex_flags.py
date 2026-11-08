"""A queue 4 (Gate G1): rules.check on Alex's real data fires X1-X4, and X5 for ibuprofen (PLAN P5)."""
import json
import pathlib
from datetime import date

from core import rules
from core.contracts import Drug, Flag, Lab, Profile

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _alex() -> Profile:
    return Profile.model_validate_json((ROOT / "data" / "alex_profile.json").read_text())


def _by_key(flags):
    return {f.key: f for f in flags}


def test_discharge_meds_give_exactly_x1_to_x4_matching_mocks():
    mock = [Flag.model_validate(f) for f in json.loads((ROOT / "mocks" / "flags.json").read_text())]
    assert rules.check_all(_alex()) == mock


def test_each_med_checked_alone():
    p = _alex()
    ids = {m.ingredient: sorted(f.id for f in rules.check(m, p)) for m in p.meds}
    assert ids == {"aspirin": [], "clopidogrel": ["X1", "X2"], "omeprazole": ["X2"],
                   "simvastatin": ["X3"], "lisinopril": ["X4"]}


def test_ibuprofen_gives_x5_on_four_exact_keys():
    flags = rules.check(Drug(ingredient="ibuprofen", dose_mg=400), _alex())
    assert {f.id for f in flags} == {"X5"}
    by = _by_key(flags)
    assert set(by) == {"aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60"}
    assert all(f.severity == "high" and not f.needs_cloud for f in flags)
    assert by["ibuprofen|egfr<60"].engine == "drug_lab"
    assert by["ibuprofen|egfr<60"].evidence == ["eGFR 48", "eGFR 62 -> 48"]
    assert by["aspirin|ibuprofen"].engine == "class_rule"
    assert by["aspirin|ibuprofen"].evidence == ["ibuprofen is an NSAID", "aspirin is an antiplatelet"]


def test_naproxen_only_through_authored_class_rule():
    """D Q17: naproxen is covered by the class rule, never by ibuprofen's keys (I4)."""
    flags = rules.check(Drug(ingredient="naproxen"), _alex())
    assert {f.key for f in flags} == {"aspirin|naproxen", "clopidogrel|naproxen", "lisinopril|naproxen"}
    assert {f.engine for f in flags} == {"class_rule"}
    assert {f.id for f in flags} == {"CR-001", "CR-002"}


def test_pantoprazole_gives_no_flag():
    assert rules.check(Drug(ingredient="pantoprazole", dose_mg=40), _alex()) == []


def test_unknown_drugs_give_no_flags():
    p = _alex()
    for name in ["codeine", "citalopram", "warfarin", "amlodipine", "st_johns_wort", "acetaminophen"]:
        assert rules.check(Drug(ingredient=name), p) == [], name


def test_case_and_whitespace_are_normalized():
    assert [f.id for f in rules.check(Drug(ingredient=" Clopidogrel "), _alex())] == ["X1", "X2"]


def test_x3_is_dose_conditioned():
    p = _alex()
    assert rules.check(Drug(ingredient="simvastatin", dose_mg=20), p) == []
    assert [f.id for f in rules.check(Drug(ingredient="simvastatin", dose_mg=40), p)] == ["X3"]
    # no dose given: use the dose already on the med list (D's eval calls check without a dose)
    [x3] = rules.check(Drug(ingredient="simvastatin"), p)
    assert x3.evidence == ["SLCO1B1 decreased function", "simvastatin 40 mg"]


def test_x3_unknown_dose_still_flags_with_note():
    p = _alex().model_copy(update={"meds": []})
    [x3] = rules.check(Drug(ingredient="simvastatin"), p)
    assert x3.id == "X3" and "dose not stated" in x3.evidence[1]


def test_x1_needs_exact_phenotype():
    p = _alex()
    p.phenotypes["CYP2C19"] = "normal_metabolizer"
    flags = rules.check(Drug(ingredient="clopidogrel"), p)
    assert [f.id for f in flags] == ["X2"]
    assert flags[0].evidence == ["omeprazole inhibits CYP2C19"]      # no gene context for a normal metabolizer


def test_x4_needs_potassium_above_threshold():
    p = _alex()
    p.labs = [lab for lab in p.labs if lab.test != "potassium"] + [
        Lab(test="potassium", value=5.2, unit="mmol/L", date=date(2025, 1, 1)),
        Lab(test="potassium", value=4.6, unit="mmol/L", date=date(2026, 11, 1))]
    assert rules.check(Drug(ingredient="lisinopril"), p) == []      # the latest result decides


def test_stale_lab_is_marked_in_evidence():
    p = _alex()
    for lab in p.labs:
        if lab.test == "potassium":
            lab.stale = True
    [x4] = rules.check(Drug(ingredient="lisinopril"), p)
    assert x4.evidence[0] == "potassium 5.2 (older than 90 days)"


def test_no_flag_evidence_says_safe():
    p = _alex()
    for name in ["ibuprofen", "naproxen", "clopidogrel", "simvastatin", "lisinopril", "omeprazole"]:
        for f in rules.check(Drug(ingredient=name), p):
            assert not any("safe" in e.lower() for e in f.evidence)
