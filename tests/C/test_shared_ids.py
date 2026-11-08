"""Agent C: one finding id can span several exact keys (A-003: X5 is four flags sharing id X5).

Regression for the bug A and D reported: app.py de-duplicated by flag.id, so typing "ibuprofen"
showed one X5 flag instead of four and hid both bleeding-risk pairs.
"""
from fastapi.testclient import TestClient

import app as app_module
from core import actions, merge
from core.contracts import Answer, Flag
from core.interfaces import load_profile

PROFILE = load_profile()

# Exactly what A's real rules.check returns for ibuprofen against Alex (agent/A-data-rules, 6e484af).
X5 = [
    Flag(id="X5", key="ibuprofen|egfr<60", severity="high", engine="drug_lab", evidence=["eGFR 48", "eGFR 62 -> 48"]),
    Flag(id="X5", key="aspirin|ibuprofen", severity="high", engine="class_rule",
         evidence=["ibuprofen is an NSAID", "aspirin is an antiplatelet"]),
    Flag(id="X5", key="clopidogrel|ibuprofen", severity="high", engine="class_rule",
         evidence=["ibuprofen is an NSAID", "clopidogrel is an antiplatelet"]),
    Flag(id="X5", key="ibuprofen|lisinopril", severity="high", engine="class_rule",
         evidence=["ibuprofen is an NSAID", "lisinopril is an ACE inhibitor", "eGFR 62 -> 48"]),
]
X5_KEYS = sorted(f.key for f in X5)


def fake_check(drug, profile):
    return list(X5) if drug.ingredient == "ibuprofen" else []


def test_ibuprofen_check_shows_all_four_x5_flags(monkeypatch):
    monkeypatch.setattr(app_module, "check", fake_check)
    flags = TestClient(app_module.app).post("/api/check", json={"text": "ibuprofen"}).json()["flags"]
    assert [f["key"] for f in flags] == X5_KEYS          # all four, ordered by (id, key)
    assert {"aspirin|ibuprofen", "clopidogrel|ibuprofen"} <= {f["key"] for f in flags}  # bleeding risk


def test_same_pair_from_both_drugs_still_appears_once(monkeypatch):
    x2 = Flag(id="X2", key="clopidogrel|omeprazole", severity="high", engine="drug_drug", evidence=[])
    monkeypatch.setattr(app_module, "check", lambda d, p: [x2] if d.ingredient in ("clopidogrel", "omeprazole") else [])
    flags = app_module._flags_for([d for d in PROFILE.meds], PROFILE)
    assert [f.key for f in flags] == ["clopidogrel|omeprazole"]


def test_reminders_and_merge_list_a_shared_id_once():
    rs = {r["id"]: r for r in actions.reminders(X5, PROFILE)}
    assert rs["r-pharmacist"]["flags"] == ["X5"]
    assert "X5, X5" not in rs["r-pharmacist"]["detail"]
    out = merge.personalize(Answer(state="no_data", text=""), X5, PROFILE)
    # X5 is about ibuprofen, which Alex doesn't take: it is described under "For you" (C-022), never "X5, X5".
    assert "For you: X5 (high)" in out and "X5, X5" not in out


def test_each_x5_key_gets_its_own_question():
    d = actions.pharmacist_draft(X5, PROFILE)
    assert "Should we review aspirin 81 mg and ibuprofen together?" in d
    assert "Should we review clopidogrel 75 mg and ibuprofen together?" in d
    assert "Should we review ibuprofen and lisinopril 10 mg together?" in d


def test_lowercase_lab_token_matches_profile_lab_once():
    egfr = X5[0]
    q = actions.question_for(egfr, PROFILE)
    assert q.count("eGFR 62 → 48") == 1
    labs = next(r for r in actions.reminders(X5, PROFILE) if r["id"] == "r-labs")
    assert labs["detail"] == "Ask your doctor whether your eGFR should be rechecked, and when."
