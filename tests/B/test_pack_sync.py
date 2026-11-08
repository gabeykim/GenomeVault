"""Stretch: bulk knowledge-pack sync (F6, F8, E4)."""
import json

import pytest

from core import cloud, kb, ledger, router
from core.contracts import Flag
from core.decoys import load_aliases, load_buckets
from core.generalize import topic_for_key

X5 = Flag(id="X5", key="ibuprofen|lisinopril", severity="high", engine="drug_drug",
          evidence=["ibuprofen with lisinopril"], needs_cloud=True)


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DELAY_S",
              "GV_COVER_INTERVAL_S"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_transport", None)
    monkeypatch.setattr(cloud, "_last_failure", None)
    (tmp_path / "all.json").write_text(json.dumps({k: f"General fact about {k}." for b in load_buckets()
                                                   for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    cloud.set_offline(None)
    ledger.reset()
    kb.reset()


def test_sync_fetches_whole_partition_as_cover():
    buckets = load_buckets()
    r = router.sync_pack()
    assert r == {"sent": len(buckets), "blocked": 0, "skipped": 0,
                 "facts": 8 * len(buckets) + len(load_aliases()), "offline": False}  # + alias copies (v5)
    entries = ledger.feed(0)
    assert [e.kind for e in entries] == ["cover"] * len(buckets)
    assert {e.bucket_id for e in entries} == {b.id for b in buckets}   # every bucket exactly once
    assert all(e.personal_fields_sent == 0 for e in entries)
    for e in entries:                                                  # buckets sent whole (I5)
        b = next(b for b in buckets if b.id == e.bucket_id)
        assert ledger.outbound(e.seq) == [topic_for_key(k).text for k in b.keys]


def test_warm_pack_answers_offline_with_zero_bytes():
    router.sync_pack()
    n = len(ledger.feed(0))
    cloud.set_offline(True)
    a = router.route("Can I take ibuprofen with lisinopril?", [X5])
    assert a.state == "known" and not a.sent_to_cloud
    assert [e.kind for e in ledger.feed(0)[n:]] == ["kb_hit"]


def test_second_sync_skips_fresh_buckets():
    router.sync_pack()
    n = len(ledger.feed(0))
    r = router.sync_pack()
    assert r["sent"] == 0 and r["skipped"] == len(load_buckets())
    assert len(ledger.feed(0)) == n
    r = router.sync_pack(skip_fresh=False)
    assert r["sent"] == len(load_buckets())


def test_order_is_shuffled_not_fixed():
    orders = set()
    for _ in range(5):
        ledger.reset()
        router.sync_pack(skip_fresh=False)
        orders.add(tuple(e.bucket_id for e in ledger.feed(0)))
    assert len(orders) > 1


def test_sync_independent_of_questions():
    """Asking a question first changes nothing about what the sync sends, beyond skipping
    buckets that were already sent whole."""
    router.route("Can I take ibuprofen with lisinopril?", [X5])
    asked = ledger.feed(0)[0].bucket_id
    r = router.sync_pack()
    sent = {e.bucket_id for e in ledger.feed(0)[1:]}
    assert sent == {b.id for b in load_buckets()} - {asked}
    assert r["skipped"] == 1


def test_offline_sends_nothing():
    cloud.set_offline(True)
    assert router.sync_pack()["offline"] is True
    assert ledger.feed(0) == [] and kb.all_facts() == []


def test_unreachable_cloud_stops(monkeypatch):
    monkeypatch.delenv("DEMO")                                  # live, no key -> unavailable
    r = router.sync_pack()
    assert r["offline"] is True and r["sent"] == 0
    assert ledger.feed(0) == []


def test_blocked_buckets_store_nothing(monkeypatch):
    monkeypatch.setattr(router, "leaks", lambda *a, **k: ["stent"])
    r = router.sync_pack()
    assert r["blocked"] == len(load_buckets()) and r["sent"] == 0
    assert kb.all_facts() == []
    assert all(e.kind == "blocked" and e.bytes_out == 0 for e in ledger.feed(0))
