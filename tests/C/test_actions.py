"""Agent C: actions (BRIEF C queue 6, F7): pharmacist draft, visit summary, reminders."""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module
from core import actions
from core.contracts import Flag
from core.interfaces import load_profile

MOCKS = Path(__file__).resolve().parents[2] / "mocks"
PROFILE = load_profile()
FLAGS = [Flag.model_validate(f) for f in json.loads((MOCKS / "flags.json").read_text())]
TODAY = date(2026, 11, 8)
client = TestClient(app_module.app)

# I7: no "safe" wording, no start/stop/switch/dose instructions.
BANNED = re.compile(r"\bsafe(r|st|ly)?\b|\b(stop|start|quit|discontinue|resume)\s+taking\b|\bswitch (to|from)\b"
                    r"|\b(increase|decrease|lower|raise|double|halve) (your|the) dose\b", re.I)


def all_text():
    s = actions.visit_summary(FLAGS, PROFILE, ["What should I bring up?"], TODAY)
    rs = actions.reminders(FLAGS, PROFILE, TODAY)
    return "\n".join([actions.pharmacist_draft(FLAGS, PROFILE), actions.summary_text(s),
                      *(r["title"] + " " + r["detail"] for r in rs), actions.reminders_ics(rs)])


def test_pharmacist_draft_lists_meds_and_every_flag_as_a_question():
    d = actions.pharmacist_draft(FLAGS, PROFILE)
    assert "clopidogrel 75 mg" in d and "omeprazole 20 mg" in d and "penicillin" in d
    numbered = [l for l in d.splitlines() if re.match(r"^\d+\. ", l)]
    assert len(numbered) == len(FLAGS)
    assert all(l.rstrip().endswith("?") for l in numbered)
    assert numbered[0].startswith("1. My CYP2C19 result is poor metabolizer (*2/*2)")  # high first
    assert "I haven't changed anything I take." in d
    assert "Demo, not medical advice" in d


def test_drug_lab_question_uses_lab_trend():
    x4 = next(f for f in FLAGS if f.id == "X4")
    q = actions.question_for(x4, PROFILE)
    assert "potassium 5.2" in q and "eGFR 62 → 48" in q and "lisinopril 10 mg" in q


def test_visit_summary_has_one_page_sections():
    s = actions.visit_summary(FLAGS, PROFILE, ["What should I bring up?"], TODAY)
    heads = [sec["heading"] for sec in s["sections"]]
    assert heads == ["Current medications", "Conditions and allergies", "Pharmacogenomic results",
                     "Recent labs", "To discuss", "Questions I asked GenomeVault"]
    genes = next(sec for sec in s["sections"] if sec["heading"] == "Pharmacogenomic results")["items"]
    assert "CYP2C19 *2/*2: poor metabolizer (notable)" in genes
    assert "CYP2D6 *1/*1: normal metabolizer" in genes
    assert s["prepared"] == "2026-11-08"
    assert "never tells you to start or stop" in s["note"]


def test_reminders_are_prompts_to_talk_not_to_change_meds():
    rs = actions.reminders(FLAGS, PROFILE, TODAY)
    by_id = {r["id"]: r for r in rs}
    assert by_id["r-pharmacist"]["due"] == "2026-11-09" and by_id["r-pharmacist"]["flags"] == ["X1", "X2"]
    assert "potassium and eGFR" in by_id["r-labs"]["detail"]
    assert by_id["r-visit"]["flags"] == ["X1", "X2", "X3", "X4"]


def test_no_flags_means_no_flag_reminders():
    assert actions.reminders([], PROFILE, TODAY) == []


def test_calendar_file_carries_no_health_details():
    ics = actions.reminders_ics(actions.reminders(FLAGS, PROFILE, TODAY),
                                now=datetime(2026, 11, 8, 12, tzinfo=timezone.utc))
    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.endswith("END:VCALENDAR\r\n")
    assert ics.count("BEGIN:VEVENT") == 3
    assert "DTSTART;VALUE=DATE:20261109" in ics
    private = [m.ingredient for m in PROFILE.meds] + list(PROFILE.genotypes) + PROFILE.conditions \
        + PROFILE.allergies + [l.test for l in PROFILE.labs] + ["X1", "X2", "X3", "X4", "5.2", "48"]
    leaked = [p for p in private if re.search(rf"\b{re.escape(p)}\b", ics, re.I)]
    assert leaked == [], f"calendar syncs to the cloud; leaked {leaked}"


def test_no_action_text_breaks_i7():
    assert not BANNED.search(all_text())


def test_action_endpoints():
    assert "clopidogrel" in client.get("/api/actions/pharmacist").json()["text"]
    s = client.get("/api/actions/summary").json()
    assert s["sections"] and s["text"].startswith("Visit summary")
    assert client.get("/api/actions/reminders").json()["reminders"]
    r = client.get("/api/actions/reminders.ics")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/calendar")
    assert "attachment" in r.headers["content-disposition"]


def test_asked_questions_reach_the_summary():
    client.post("/api/ask", json={"question": "Is my statin dose a problem?"})
    s = client.get("/api/actions/summary").json()
    asked = next(sec for sec in s["sections"] if sec["heading"] == "Questions I asked GenomeVault")
    assert "Is my statin dose a problem?" in asked["items"]


def test_printable_summary_is_self_contained_and_escaped():
    client.post("/api/ask", json={"question": "<script>alert(1)</script>"})
    page = client.get("/summary").text
    assert page.startswith("<!doctype html>") and "Visit summary" in page
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert not re.search(r"(src|href)\s*=\s*[\"']?(https?:)?//", page)
    assert not re.search(r"\bsafe\b", page, re.I)
