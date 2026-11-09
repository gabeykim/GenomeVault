"""Post-G2 check (PR #2 + PR #3 merged): B's privacy guarantees hold through C's real app path,
not just when route() is called directly. POST /api/ask -> app builds flags -> router.route ->
cloud (DEMO=1 replay, I8) -> real ledger. Every text that left must pass I3 with the real profile,
the app's outbound view must show exactly what the ledger recorded (F5/S4), and the offline switch
must stop all bucket traffic (F8/S6)."""
import json

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core import cloud, kb, ledger
from core.decoys import load_buckets
from core.graph import load_profile
from core.validator import _key_drugs, check_outbound, wording_problems

def test_app_uses_real_router_and_ledger():
    # PR #2 + #3 are on main (D-032): a silent skip here would hide a regression to stand-ins.
    # LEDGER_IS_MOCK is read with getattr because C may drop it (PR #8 keeps it as False).
    assert app_module.MODES.get("router.route") == "real"
    assert not getattr(app_module, "LEDGER_IS_MOCK", False)
    assert "mock" not in app_module.MODES.values()


client = TestClient(app_module.app)

# C's demo chips (D's eval texts) plus brand, combination, local-only and off-list questions.
QUESTIONS = [
    "What should I bring up with my cardiologist?",
    "Which of my new prescriptions should I ask my pharmacist about first?",
    "Could pantoprazole work instead of omeprazole with my clopidogrel?",
    "Can I take ibuprofen for a headache?",
    "Is anything on my discharge list a problem with my genetics?",
    "Can I take Advil with my Plavix?",
    "Is my simvastatin dose OK for my genes?",
    "Can I take Aleve?",
    "Is lisinopril OK with my other medicines?",
    "Can I take amoxicillin?",
]


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_GRAPH_DB"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    for b in load_buckets():
        (tmp_path / f"{b.id}.json").write_text(
            json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    cloud.set_offline(None)
    ledger.reset()
    kb.reset()


def _bucket_allow(bucket_id: str) -> set[str]:
    from core.decoys import TAIL_VERSION
    bucket = next(b for b in load_buckets() + load_buckets(TAIL_VERSION) if b.id == bucket_id)
    return set().union(*(_key_drugs(k) for k in bucket.keys))


def test_every_text_sent_through_the_app_passes_i3():
    profile = load_profile()
    genotypes = [g for g in profile.genotypes.values() if g]
    for q in QUESTIONS:
        r = client.post("/api/ask", json={"question": q})
        assert r.status_code == 200, q
    entries = [e for e in ledger.feed(0) if e.kind == "bucket"]
    assert entries, "the demo questions on a cold KB must send at least one bucket (S4)"
    for e in entries:
        texts = ledger.outbound(e.seq)
        assert len(texts) == 8 and len(set(texts)) == 8          # whole bucket (I5)
        assert e.personal_fields_sent == 0
        assert check_outbound(texts, profile, allow=_bucket_allow(e.bucket_id))   # I3
        for t in texts:
            assert not any(g in t for g in genotypes)
    totals = client.get("/api/ledger").json()["totals"]
    assert totals["personal_fields_sent"] == 0
    assert totals["count"] == len(ledger.feed(0))


def test_app_outbound_view_matches_the_ledger_exactly():
    client.post("/api/ask", json={"question": QUESTIONS[0]})
    entries = [e for e in ledger.feed(0) if e.kind == "bucket"]
    assert entries
    for e in entries:
        shown = client.get(f"/api/ledger/{e.seq}/outbound").json()
        assert shown["available"] is True
        assert shown["texts"] == ledger.outbound(e.seq)          # S4: what you see is what left


def test_repeat_question_through_the_app_sends_nothing_new():
    client.post("/api/ask", json={"question": QUESTIONS[0]})
    sent = sum(e.bytes_out for e in ledger.feed(0))
    again = client.post("/api/ask", json={"question": QUESTIONS[0]}).json()
    assert again["sent_to_cloud"] is False                       # KB hit (F6, S4 repeat)
    assert sum(e.bytes_out for e in ledger.feed(0)) == sent


def test_offline_switch_stops_all_bucket_traffic():
    assert client.post("/api/offline", json={"offline": True}).status_code == 200
    for q in QUESTIONS:
        r = client.post("/api/ask", json={"question": q}).json()
        assert r["sent_to_cloud"] is False, q
    assert sum(e.bytes_out for e in ledger.feed(0)) == 0         # F8/S6: nothing leaves


def test_app_answers_never_break_i7():
    for q in QUESTIONS:
        text = client.post("/api/ask", json={"question": q}).json()["text"]
        assert not wording_problems(text), (q, wording_problems(text))


# I4 (human report 2026-11-08 16:45): a named pair outside the partition, with no fact and no flag on
# that exact pair, must read no_data, not "checked on your device" just because a flag shares a drug.
UNCOVERED_PAIR = "Is pantoprazole okay with my lisinopril?"


def test_uncovered_named_pair_is_no_data_not_checked():
    from core.decoys import bucket_for, universe
    from core.router import LOCAL_TEXT
    key = "lisinopril|pantoprazole"
    assert key not in universe() and bucket_for(key) is None     # precondition: truly uncovered
    r = client.post("/api/ask", json={"question": UNCOVERED_PAIR}).json()
    assert r["state"] == "no_data", r
    assert LOCAL_TEXT not in r["text"] and "checked on your device" not in r["text"].lower()
    assert r["facts"] == []
    assert not wording_problems(r["text"])


def test_uncovered_named_pair_offline_is_no_data():
    from core.router import LOCAL_TEXT
    assert client.post("/api/offline", json={"offline": True}).status_code == 200
    r = client.post("/api/ask", json={"question": UNCOVERED_PAIR}).json()
    assert r["state"] == "no_data" and r["sent_to_cloud"] is False, r
    assert LOCAL_TEXT not in r["text"]


def test_covered_pantoprazole_pair_still_known():
    r = client.post("/api/ask", json={"question": "Is pantoprazole okay with my clopidogrel?"}).json()
    assert r["state"] == "known", r
    assert any(f["key"] == "clopidogrel|pantoprazole" for f in r["facts"])
