"""Queue 8: random delays (P6.4) and cover buckets (P6.6), gate G3."""
import json
import threading
import time

import httpx
import pytest

from core import cloud, kb, ledger, router
from core.contracts import Flag
from core.decoys import bucket_for, load_buckets
from core.generalize import topic_for_key
from core.interfaces import load_profile
from core.validator import check_outbound

X1 = Flag(id="X1", key="CYP2C19:poor_metabolizer|clopidogrel", severity="high", engine="gene_drug",
          evidence=["CYP2C19 poor metabolizer"], needs_cloud=True)


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    """DEMO=1 replay from a cache answering every key of the partition."""
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
    router.stop_cover()
    ledger.reset()
    kb.reset()


# --- P6.4 random delays ---------------------------------------------------------------------------

def test_delay_defaults_live_and_demo(monkeypatch):
    assert cloud.delay_range() == (0.0, 0.0)            # demo: nothing leaves, no point waiting
    monkeypatch.delenv("DEMO")
    assert cloud.delay_range() == cloud.LIVE_DELAY_S
    lo, hi = cloud.LIVE_DELAY_S
    assert 0 < lo < hi


def test_delay_env_and_validation(monkeypatch):
    monkeypatch.setenv("GV_DELAY_S", "0.1,0.4")
    assert cloud.delay_range() == (0.1, 0.4)
    for bad in ("-1,2", "3,1", "x"):
        monkeypatch.setenv("GV_DELAY_S", bad)
        with pytest.raises(ValueError):
            cloud.delay_range()


def test_live_pauses_before_every_request_with_random_lengths(monkeypatch):
    slept = []
    order = []
    monkeypatch.setattr(cloud, "_sleep", lambda s: (slept.append(s), order.append("sleep")))

    def handler(request):
        order.append("request")
        return httpx.Response(200, json={"content": [{"type": "text", "text": "general answer"}]})

    monkeypatch.delenv("DEMO")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GV_DELAY_S", "0.5,3")
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(handler))
    b = load_buckets()[0]
    facts = cloud.ask_bucket(b, [topic_for_key(k) for k in b.keys])
    assert len(facts) == 8
    assert order == ["sleep", "request"] * 8
    assert all(0.5 <= s <= 3 for s in slept)
    assert len(set(slept)) > 1                          # random, not a fixed beat


def test_demo_pauses_only_when_asked(monkeypatch):
    slept = []
    monkeypatch.setattr(cloud, "_sleep", slept.append)
    b = load_buckets()[0]
    cloud.ask_bucket(b, [topic_for_key(k) for k in b.keys])
    assert slept == []
    monkeypatch.setenv("GV_DELAY_S", "0.01,0.02")
    cloud.ask_bucket(b, [topic_for_key(k) for k in b.keys])
    assert len(slept) == 8


def test_two_bucket_question_is_spread_out(monkeypatch):
    slept = []
    monkeypatch.setattr(cloud, "_sleep", slept.append)
    monkeypatch.setenv("GV_DELAY_S", "0.2,1")
    a = router.route("And clopidogrel with pantoprazole?", [X1])
    sends = [e for e in ledger.feed(0) if e.kind == "bucket"]
    assert len(sends) == 2 and a.sent_to_cloud
    assert len(slept) == 16                              # one pause per outbound request


# --- P6.6 cover buckets ---------------------------------------------------------------------------

def test_send_cover_sends_one_whole_fixed_bucket():
    e = router.send_cover()
    assert e is not None and e.kind == "cover" and e.bytes_out > 0 and e.personal_fields_sent == 0
    b = next(b for b in load_buckets() if b.id == e.bucket_id)
    texts = ledger.outbound(e.seq)
    assert texts == [topic_for_key(k).text for k in b.keys]     # the partition's bucket, untouched (I5)
    allow = set()
    for k in b.keys:
        allow |= router._key_drugs(k)
    assert check_outbound(texts, load_profile(), allow=sorted(allow))
    assert all(kb.get(k) is not None for k in b.keys)          # all 8 answers stored


def test_cover_choice_ignores_questions_and_covers_partition():
    router.route("Does my genetics change how clopidogrel works for me?", [X1])
    real = bucket_for(X1.key).id
    seen = [router.send_cover().bucket_id for _ in range(400)]
    ids = {b.id for b in load_buckets()}
    assert set(seen) == ids                                     # every bucket shows up as cover
    # uniform: the real question's bucket is not over-represented
    assert seen.count(real) < 3 * len(seen) / len(ids)


def test_cover_is_nothing_while_offline():
    cloud.set_offline(True)
    try:
        assert router.send_cover() is None
    finally:
        cloud.set_offline(None)
    assert ledger.feed(0) == []


def test_cover_unreachable_cloud_sends_nothing(monkeypatch):
    monkeypatch.delenv("DEMO")                                  # live, no key -> unavailable
    assert router.send_cover() is None
    assert ledger.feed(0) == []


def test_cover_blocked_by_leakage_check(monkeypatch):
    monkeypatch.setattr(router, "leaks", lambda *a, **k: ["stent"])
    e = router.send_cover()
    assert e.kind == "blocked" and e.bytes_out == 0
    assert kb.all_facts() == []


def test_cover_entries_are_distinct_from_real_sends():
    router.route("Does my genetics change how clopidogrel works for me?", [X1])
    router.send_cover()
    assert [e.kind for e in ledger.feed(0)] == ["bucket", "cover"]


def test_steady_schedule_thread_start_stop():
    assert not router.cover_running()
    assert router.start_cover(0.02)
    assert not router.start_cover(0.02)                         # already running
    deadline = time.time() + 3
    while time.time() < deadline and len(ledger.feed(0)) < 3:
        time.sleep(0.01)
    router.stop_cover()
    assert not router.cover_running()
    n = len(ledger.feed(0))
    assert n >= 3 and all(e.kind == "cover" for e in ledger.feed(0))
    time.sleep(0.1)
    assert len(ledger.feed(0)) == n                             # really stopped


def test_schedule_survives_errors(monkeypatch):
    calls = threading.Event()
    count = []

    def flaky():
        count.append(1)
        if len(count) >= 3:
            calls.set()
        raise RuntimeError("boom")

    monkeypatch.setattr(router, "send_cover", flaky)
    router.start_cover(0.01)
    assert calls.wait(3)
    assert router.cover_running()
    router.stop_cover()


def test_interval_env(monkeypatch):
    assert router.cover_interval() == router.DEFAULT_COVER_INTERVAL_S
    monkeypatch.setenv("GV_COVER_INTERVAL_S", "5")
    assert router.cover_interval() == 5
    monkeypatch.setenv("GV_COVER_INTERVAL_S", "0")
    with pytest.raises(ValueError):
        router.cover_interval()
    with pytest.raises(ValueError):
        router.start_cover(0)
