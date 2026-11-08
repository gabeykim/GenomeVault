"""Agent C: PLAN v1.2 / D-021 in the UI layer.

- CYP2D6 is `not_assessed` (not callable from SNP data): shown as "not assessed", never as a notable result.
- aspirin|clopidogrel after a stent is expected DAPT: an informational note from A's rules, never a Flag.
"""
import re
from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module
from core import actions
from core.interfaces import load_profile

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app_module.app)

DAPT = {"id": "EX-001", "key": "aspirin|clopidogrel", "source": "ACC/AHA DAPT guideline (2016 focused update)",
        "text": "Aspirin with clopidogrel is dual antiplatelet therapy, the usual plan after a coronary stent. "
                "It is listed here for information, not as a warning; how long to continue it is a question "
                "for the cardiologist."}


def _profile_with_cyp2d6_not_assessed():
    p = load_profile().model_copy(deep=True)
    p.genotypes["CYP2D6"] = "not_assessed"
    p.phenotypes["CYP2D6"] = "not_assessed"
    return p


def test_summary_shows_not_assessed_gene_neutrally():
    s = actions.visit_summary([], _profile_with_cyp2d6_not_assessed())
    genes = next(sec for sec in s["sections"] if sec["heading"] == "Pharmacogenomic results")["items"]
    assert "CYP2D6: not assessed by this test" in genes
    assert not any("CYP2D6" in g and "notable" in g for g in genes)


def test_not_assessed_helper():
    assert actions.not_assessed("not_assessed") and actions.not_assessed("Indeterminate")
    assert not actions.not_assessed("poor_metabolizer") and not actions.not_assessed(None)


def test_ui_treats_not_assessed_as_neutral():
    js = (ROOT / "ui" / "app.js").read_text()
    assert "NOT_ASSESSED" in js and '"v hot na"' in js


def test_flags_endpoint_carries_dapt_note_not_a_flag(monkeypatch):
    monkeypatch.setattr(app_module, "expected_notes_all", lambda profile: [DAPT, dict(DAPT)])  # dup collapses
    data = client.get("/api/flags").json()
    assert [n["key"] for n in data["notes"]] == ["aspirin|clopidogrel"]
    assert "aspirin|clopidogrel" not in {f["key"] for f in data["flags"]}
    assert "not as a warning" in data["notes"][0]["text"]


def test_typed_check_carries_note(monkeypatch):
    monkeypatch.setattr(app_module, "expected_notes", lambda drug, profile: [DAPT] if drug.ingredient == "aspirin" else [])
    data = client.post("/api/check", json={"text": "aspirin"}).json()
    assert data["notes"] and data["notes"][0]["id"] == "EX-001"


def test_notes_pass_the_i7_guard(monkeypatch):
    bad = {**DAPT, "text": "This pair is safe. It is the usual plan after a stent."}
    monkeypatch.setattr(app_module, "expected_notes_all", lambda profile: [bad])
    text = client.get("/api/flags").json()["notes"][0]["text"]
    assert not re.search(r"\bsafe\b", text, re.I) and "usual plan" in text


def test_summary_lists_note_as_information(monkeypatch):
    monkeypatch.setattr(app_module, "expected_notes_all", lambda profile: [DAPT])
    s = client.get("/api/actions/summary").json()
    info = next(sec for sec in s["sections"] if sec["heading"] == "For information (not a warning)")
    assert info["items"][0].startswith("Aspirin with clopidogrel is dual antiplatelet therapy")


def test_no_notes_without_a_rules_module():
    if app_module.expected_notes_all is None:
        assert client.get("/api/flags").json()["notes"] == []
