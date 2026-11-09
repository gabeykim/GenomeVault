"""D-040 part 3: GV_DEMO_LIVE_FALLBACK=1 with DEMO=1 asks a bucket with a cache miss live, whole (I5)."""
import json

import httpx
import pytest

from core import cloud
from core.decoys import load_buckets
from core.generalize import topic_for_key


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for v in ("ANTHROPIC_API_KEY", "GV_CLOUD_MODEL", "GV_CLOUD_URL", "GV_OFFLINE", "GV_DELAY_S",
              "GV_DEMO_LIVE_FALLBACK"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_last_failure", None)
    monkeypatch.setattr(cloud, "_sleep", lambda s: None)


class Rec:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def __call__(self, request):
        self.sent.append(json.loads(request.content)["messages"][0]["content"])
        if self.fail:
            raise httpx.ConnectError("down", request=request)
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Live general answer."}]})


def _setup(monkeypatch, tmp_path, cached: int, fail=False):
    rec = Rec(fail)
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(rec))
    b = load_buckets()[0]
    (tmp_path / "c.json").write_text(json.dumps({k: "Cached general answer." for k in b.keys[:cached]}))
    return b, [topic_for_key(k) for k in b.keys], rec


def test_flag_off_never_touches_network(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3)
    facts = cloud.ask_bucket(b, topics)
    assert rec.sent == [] and [f.key for f in facts] == b.keys[:3]      # I8 unchanged


def test_miss_sends_whole_bucket_live_and_keeps_cached_answers(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GV_CLOUD_MODEL", "m")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3)
    facts = {f.key: f for f in cloud.ask_bucket(b, topics)}
    assert rec.sent == [t.text for t in topics]                         # all 8, not just the misses (I5)
    assert sorted(facts) == sorted(b.keys)
    for k in b.keys[:3]:
        assert facts[k].text == "Cached general answer." and facts[k].source.startswith("cloud-cache:")
    for k in b.keys[3:]:
        assert facts[k].text == "Live general answer." and facts[k].source == "cloud:m"


def test_full_cache_hit_stays_offline(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=8)
    assert len(cloud.ask_bucket(b, topics)) == 8 and rec.sent == []


def test_no_key_replays_only(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3)
    assert len(cloud.ask_bucket(b, topics)) == 3 and rec.sent == []


def test_forced_offline_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3)
    cloud.set_offline(True)
    with pytest.raises(cloud.CloudUnavailable):
        cloud.ask_bucket(b, topics)
    assert rec.sent == []


def test_live_failure_degrades_to_replay(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3, fail=True)
    facts = cloud.ask_bucket(b, topics)
    assert [f.key for f in facts] == b.keys[:3]                          # misses stay no_data (I4)
    assert cloud.status()["online"] is True                              # demo still answers from replay


def test_live_fallback_uses_live_delays(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    slept = []
    b, topics, rec = _setup(monkeypatch, tmp_path, cached=3)
    monkeypatch.setattr(cloud, "_sleep", slept.append)
    cloud.ask_bucket(b, topics)
    lo, hi = cloud.LIVE_DELAY_S
    assert len(slept) == 8 and all(lo <= s <= hi for s in slept)        # replay pauses are 0 (skipped)


def test_live_fallback_answers_pass_i7(monkeypatch, tmp_path):
    monkeypatch.setenv("GV_DEMO_LIVE_FALLBACK", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b, topics, _ = _setup(monkeypatch, tmp_path, cached=0)
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(
        lambda r: httpx.Response(200, json={"content": [{"type": "text", "text": "This combination is safe."}]})))
    assert cloud.ask_bucket(b, topics) == []
