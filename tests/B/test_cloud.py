import json
from datetime import date, timedelta

import httpx
import pytest

from core import cloud
from core.decoys import load_buckets
from core.generalize import topic_for_key
from core.contracts import Topic


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ("DEMO", "ANTHROPIC_API_KEY", "GV_CLOUD_MODEL", "GV_CLOUD_URL", "GV_CLOUD_TTL_DAYS", "GV_CLOUD_CACHE",
              "GV_OFFLINE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_transport", None)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_last_failure", None)


def _bucket():
    return load_buckets()[0]


def _topics(b):
    return [topic_for_key(k) for k in b.keys]


class Recorder:
    """Mock Messages API. Records every request and which client (session) sent it."""
    def __init__(self, status=200):
        self.requests = []
        self.status = status

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": "x"})
        body = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": f"answer to: {body['messages'][0]['content']}"}]})


def test_live_one_request_per_topic_single_turn_cloud_facts(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(rec))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GV_CLOUD_MODEL", "model-x")
    b = _bucket()
    facts = cloud.ask_bucket(b, _topics(b))

    assert len(rec.requests) == 8                       # one concept per request (P6.4)
    assert [f.key for f in facts] == b.keys            # all 8 answers back (P6.5)
    for req, t in zip(rec.requests, _topics(b)):
        body = json.loads(req.content)
        assert body["model"] == "model-x"
        assert body["messages"] == [{"role": "user", "content": t.text}]   # single turn, Topic text only
        assert req.headers["x-api-key"] == "test-key"
    for f in facts:
        assert f.tier == "cloud" and f.source == "cloud:model-x"
        assert f.fetched == date.today() and f.expires == date.today() + timedelta(days=30)


def test_ttl_from_env(monkeypatch):
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(Recorder()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GV_CLOUD_TTL_DAYS", "7")
    b = _bucket()
    f = cloud.ask_bucket(b, _topics(b)[:1])[0]
    assert f.expires - f.fetched == timedelta(days=7)


def test_rejects_topics_outside_bucket(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b0, b1 = load_buckets()[:2]
    with pytest.raises(ValueError):
        cloud.ask_bucket(b0, [topic_for_key(b1.keys[0])])


def test_no_key_is_unavailable():
    b = _bucket()
    with pytest.raises(cloud.CloudUnavailable):
        cloud.ask_bucket(b, _topics(b))


def test_http_error_is_unavailable(monkeypatch):
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(Recorder(status=500)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b = _bucket()
    with pytest.raises(cloud.CloudUnavailable):
        cloud.ask_bucket(b, _topics(b))


def test_network_down_is_unavailable(monkeypatch):
    def down(request):
        raise httpx.ConnectError("offline", request=request)
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(down))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    b = _bucket()
    with pytest.raises(cloud.CloudUnavailable):
        cloud.ask_bucket(b, _topics(b))


def test_demo_replays_cache_without_network(monkeypatch, tmp_path):
    def boom(request):
        raise AssertionError("demo mode touched the network (I8)")
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(boom))
    b = _bucket()
    (tmp_path / "b01.json").write_text(json.dumps({b.keys[0]: "cached one", b.keys[1]: "  "}))
    (tmp_path / "extra.json").write_text(json.dumps({b.keys[2]: "cached three"}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    facts = cloud.ask_bucket(b, _topics(b))
    # missing or blank keys get no Fact (router → no_data, I4)
    assert {f.key: f.text for f in facts} == {b.keys[0]: "cached one", b.keys[2]: "cached three"}
    assert all(f.tier == "cloud" and f.source == f"cloud-cache:{b.version}" for f in facts)


def test_demo_with_empty_cache_returns_nothing(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path / "missing"))
    b = _bucket()
    assert cloud.ask_bucket(b, _topics(b)) == []


def test_malformed_cache_is_an_error(monkeypatch, tmp_path):
    (tmp_path / "bad.json").write_text(json.dumps(["not", "a", "dict"]))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    b = _bucket()
    with pytest.raises(ValueError):
        cloud.ask_bucket(b, _topics(b))


def test_record_writes_one_file_per_bucket_and_replays(monkeypatch, tmp_path):
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(Recorder()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    n = cloud.record(tmp_path)
    buckets = load_buckets()
    assert n == 8 * len(buckets)
    assert sorted(p.stem for p in tmp_path.glob("*.json")) == sorted(b.id for b in buckets)
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    b = buckets[3]
    assert [f.key for f in cloud.ask_bucket(b, _topics(b))] == b.keys


def test_system_prompt_respects_I7():
    p = cloud.SYSTEM_PROMPT.lower()
    assert "do not say anything is safe" in p and "start, stop" in p


def test_live_request_turns_thinking_off_and_has_room_to_answer(monkeypatch):
    """D-026: thinking off via `between_tools` (the API rejects `disabled`), 1000 output tokens."""
    rec = Recorder()
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(rec))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    b = _bucket()
    cloud.ask_bucket(b, _topics(b)[:1])
    body = json.loads(rec.requests[0].content)
    assert body["thinking"] == {"type": "between_tools"}
    assert body["max_tokens"] == 1000


def test_empty_max_tokens_reply_is_logged_not_silent(monkeypatch, caplog):
    """D-026: a reply holding only an empty thinking block reads as no_data (I4) and is logged."""
    def thinking_only(request):
        return httpx.Response(200, json={"content": [{"type": "thinking", "thinking": ""}],
                                         "stop_reason": "max_tokens"})
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(thinking_only))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    b = _bucket()
    t = _topics(b)[0]
    with caplog.at_level("WARNING", logger="core.cloud"):
        facts = cloud.ask_bucket(b, [t])
    assert facts == []
    msgs = [r.getMessage() for r in caplog.records if r.name == "core.cloud"]
    assert len(msgs) == 1 and t.key in msgs[0] and "max_tokens" in msgs[0]


def test_system_prompt_asks_for_neutral_reporting_style():
    """D-027 note: the pack was recorded with this sentence so guideline descriptions pass I7."""
    p = cloud.SYSTEM_PROMPT
    assert "neutral reporting style" in p
    assert "Never write is recommended, are advised, is preferred, should" in p


def test_only_topics_accepted_no_profile_parameter():
    import inspect
    assert list(inspect.signature(cloud.ask_bucket).parameters) == ["bucket", "topics"]
