"""G3 prep (KB + knowledge pack, D-027): B's pack guarantees hold through C's real app path.
POST /api/sync -> app thread -> router.sync_pack -> cloud (DEMO=1 replay, I8) -> real KB + ledger.
The pack must be the whole fixed partition (I5), every text must pass I3, the app must label those
rows as pack and never mark one as "yours", and after a sync the offline switch must leave the
demo questions answered on-device with 0 bytes (F6, F8, S6)."""
import json
import time

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core import cloud, kb, ledger
from core.decoys import load_buckets
from core.graph import load_profile
from core.validator import _key_drugs, check_outbound

def test_app_uses_real_router_ledger_and_pack():
    # Real on main since D-032; fail loudly instead of skipping if the app falls back.
    assert app_module.MODES.get("router.route") == "real"
    assert not getattr(app_module, "LEDGER_IS_MOCK", False)
    assert app_module.sync_pack is not None


client = TestClient(app_module.app)

QUESTIONS = [
    "What should I bring up with my cardiologist?",
    "Could pantoprazole work instead of omeprazole with my clopidogrel?",
    "Can I take ibuprofen for a headache?",
    "Is my simvastatin dose OK for my genes?",
    "Can I take Advil with my Plavix?",
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
    app_module._pack_seqs.clear()
    app_module._sync.update(running=False, result=None, finished=None)
    yield
    cloud.set_offline(None)
    ledger.reset()
    kb.reset()
    app_module._pack_seqs.clear()


def _sync_and_wait() -> dict:
    r = client.post("/api/sync")
    assert r.status_code == 200, r.text
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        s = client.get("/api/sync").json()
        if not s["running"] and s["finished"]:
            return s["result"]
        time.sleep(0.02)
    raise AssertionError("sync did not finish in demo mode")


def _bucket_allow(bucket_id: str) -> set[str]:
    bucket = next(b for b in load_buckets() if b.id == bucket_id)
    return set().union(*(_key_drugs(k) for k in bucket.keys))


def test_app_sync_sends_the_whole_partition_once():
    result = _sync_and_wait()
    buckets = load_buckets()
    assert result["sent"] == len(buckets) and result["blocked"] == 0 and not result["offline"]
    rows = [e for e in ledger.feed(0) if e.bytes_out > 0]
    assert sorted(e.bucket_id for e in rows) == sorted(b.id for b in buckets)   # I5: same for all
    assert {e.seq for e in rows} <= app_module._pack_seqs


def test_app_pack_rows_pass_i3_and_are_never_marked_yours():
    _sync_and_wait()
    profile = load_profile()
    entries = client.get("/api/ledger").json()["entries"]
    sent = [e for e in entries if e["bytes_out"] > 0]
    assert sent
    for e in sent:
        assert e["pack"] is True and e["kind"] == "cover"
        assert e["personal_fields_sent"] == 0
        shown = client.get(f"/api/ledger/{e['seq']}/outbound").json()
        assert len(shown["texts"]) == 8 and len(set(shown["texts"])) == 8
        assert check_outbound(shown["texts"], profile, allow=_bucket_allow(e["bucket_id"]))   # I3
        assert shown["mine"] == []                     # pack is not the user's question


def test_after_sync_offline_questions_use_the_pack_with_zero_bytes():
    _sync_and_wait()
    sent_before = sum(e.bytes_out for e in ledger.feed(0))
    for b in load_buckets():
        for k in b.keys:
            assert kb.get(k) is not None, k          # every partition key is now on-device
    assert client.post("/api/offline", json={"offline": True}).status_code == 200
    for q in QUESTIONS:
        r = client.post("/api/ask", json={"question": q}).json()
        assert r["sent_to_cloud"] is False, q
    assert sum(e.bytes_out for e in ledger.feed(0)) == sent_before   # F8/S6: nothing new left


def test_second_app_sync_sends_nothing_new():
    _sync_and_wait()
    sent = sum(e.bytes_out for e in ledger.feed(0))
    result = _sync_and_wait()
    assert result["sent"] == 0 and result["skipped"] == len(load_buckets())
    assert sum(e.bytes_out for e in ledger.feed(0)) == sent


def test_app_refuses_sync_while_offline():
    assert client.post("/api/offline", json={"offline": True}).status_code == 200
    assert client.post("/api/sync").status_code == 409
    assert sum(e.bytes_out for e in ledger.feed(0)) == 0
