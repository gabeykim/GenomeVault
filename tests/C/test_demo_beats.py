"""Agent C: demo chips (D's exact eval texts) and the S4/S6 ledger views."""
import importlib.util
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app_module.app)

# D's demo questions (coord/inbox/to-C/20261108-1323-from-D-re-ui-look.md, eval/queries.json).
DEMO_QUESTIONS = {
    "Q18": "What should I bring up with my cardiologist?",
    "Q19": "Which of my new prescriptions should I ask my pharmacist about first?",
    "Q07": "Could pantoprazole work instead of omeprazole with my clopidogrel?",
    "Q15": "Can I take ibuprofen for a headache?",
}
REAL_ROUTER = app_module.MODES["router.route"] == "real"
HAS_KB = importlib.util.find_spec("core.kb") is not None


def _chips():
    html = (ROOT / "ui" / "index.html").read_text()
    return dict(re.findall(r'data-qid="(Q\d+)" data-q="([^"]+)"', html))


def test_chips_are_d_demo_questions():
    assert _chips() == DEMO_QUESTIONS


def test_chips_match_eval_queries_when_present():
    path = ROOT / "eval" / "queries.json"
    if not path.exists():
        pytest.skip("eval/queries.json arrives with D's branch")
    data = json.loads(path.read_text())
    rows = data if isinstance(data, list) else data.get("queries", [])
    texts = {r["id"]: r.get("text") or r.get("question") for r in rows}
    for qid, text in _chips().items():
        assert texts.get(qid) == text, f"{qid} differs from eval/queries.json"


def test_outbound_endpoint_shape():
    d = client.get("/api/ledger/999999/outbound").json()
    assert d == {"seq": 999999, "texts": [], "mine": [], "available": d["available"]}
    assert d["available"] == app_module.EXTRAS["ledger.outbound"]


def test_status_reports_extras():
    extras = client.get("/api/status").json()["extras"]
    assert set(extras) >= {"ledger.outbound", "kb.stats", "generalize.generalize",
                           "rules.expected_notes", "rules.expected_notes_all", "cloud.set_offline"}
    assert all(isinstance(v, bool) for v in extras.values())


def test_learned_is_null_without_kb_and_counts_with_it():
    learned = client.get("/api/ledger").json()["learned"]
    if not HAS_KB:
        assert learned is None
    else:
        assert {"total", "fresh"} <= set(learned)


@pytest.fixture
def filled_cache(monkeypatch, tmp_path):
    """A cloud cache with a neutral answer for every partition key (no numbers, no drug pairs)."""
    from core import decoys
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "all.json").write_text(json.dumps({k: "General guidance exists for this topic." for k in decoys.universe()}))
    monkeypatch.setenv("GV_CLOUD_CACHE", str(cache))


@pytest.mark.skipif(not (REAL_ROUTER and HAS_KB), reason="needs B's router and KB (integrated build)")
def test_s4_then_s6_end_to_end(filled_cache):
    q = DEMO_QUESTIONS["Q18"]
    first = client.post("/api/ask", json={"question": q}).json()
    assert first["sent_to_cloud"] is True
    entries = client.get("/api/ledger").json()["entries"]
    buckets = [e for e in entries if e["kind"] == "bucket"]
    assert buckets and all(e["personal_fields_sent"] == 0 for e in entries)

    out = client.get(f"/api/ledger/{buckets[0]['seq']}/outbound").json()
    assert len(out["texts"]) == 8
    assert out["mine"], "the device can tell which question was the user's"
    profile = app_module.load_profile()
    private = list(profile.genotypes.values()) + [f"{m.dose_mg:g} mg" for m in profile.meds if m.dose_mg]
    assert not [p for p in private if any(p in t for t in out["texts"])], "nothing personal left"

    learned = client.get("/api/ledger").json()["learned"]["fresh"]
    assert learned >= 8, "all 8 bucket answers are stored, decoys included"

    since = client.get("/api/ledger").json()["totals"]["count"]
    again = client.post("/api/ask", json={"question": q}).json()
    assert again["sent_to_cloud"] is False
    new = client.get(f"/api/ledger?since={since}").json()["entries"]
    assert new and all(e["kind"] == "kb_hit" and e["bytes_out"] == 0 for e in new)


def test_cover_rows_never_mark_yours(monkeypatch):
    from datetime import datetime, timezone
    from core.contracts import Flag, LedgerEntry
    row = LedgerEntry(seq=7, ts=datetime.now(timezone.utc), bucket_id="b14", kind="cover", bytes_out=900)
    monkeypatch.setattr(app_module, "ledger_feed", lambda since=0: [row] if row.seq > since else [])
    monkeypatch.setattr(app_module, "ledger_outbound", lambda seq: ["T-mine", "T-other"])
    monkeypatch.setattr(app_module, "generalize_flag", lambda f: [type("T", (), {"text": "T-mine"})()])
    assert client.get("/api/ledger/7/outbound").json()["mine"] == []           # cover: never "yours"
    row2 = row.model_copy(update={"kind": "bucket"})
    monkeypatch.setattr(app_module, "ledger_feed", lambda since=0: [row2] if row2.seq > since else [])
    assert client.get("/api/ledger/7/outbound").json()["mine"] == [0]          # a real question group: yes
