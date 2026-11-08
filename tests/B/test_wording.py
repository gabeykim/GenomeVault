"""I7 wording check on cloud answers, plus `record` resume and `check_cache` (demo cache vetting, I8)."""
import json

import httpx
import pytest

from core import cloud
from core.decoys import load_buckets, universe
from core.generalize import topic_for_key
from core.validator import check_wording, wording_problems


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ("DEMO", "ANTHROPIC_API_KEY", "GV_CLOUD_CACHE", "GV_OFFLINE", "GV_DELAY_S"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_transport", None)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_last_failure", None)


@pytest.mark.parametrize("text", [
    "This combination is generally safe.",
    "It can be used safely in most adults.",
    "There are safety concerns with high doses.",
    "Combining them is unsafe.",
    "Stop taking simvastatin if muscle pain appears.",
    "Do not take ibuprofen with warfarin.",
    "Avoid grapefruit juice.",
    "Exposure rises. You should reduce the dose.",
    "You may want to switch to another statin.",
    "Don't start clopidogrel without testing.",
])
def test_rejects_safe_and_instructions(text):
    assert not check_wording(text)
    assert wording_problems(text)


@pytest.mark.parametrize("text", [
    "Clopidogrel needs CYP2C19 to become active. Poor metabolizers form less active drug.",
    "Use of NSAIDs with warfarin raises bleeding risk across the population.",
    "Increase in simvastatin exposure is seen with SLCO1B1 decreased function.",
    "Patients who stop taking a statin lose its effect over weeks.",
    "Discuss this with a pharmacist before the next refill.",
    "Nothing is established for this combination.",
])
def test_accepts_descriptive_text(text):
    assert check_wording(text), wording_problems(text)


def _bucket():
    return load_buckets()[0]


def test_demo_replay_drops_I7_violations(monkeypatch, tmp_path):
    b = _bucket()
    (tmp_path / "x.json").write_text(json.dumps({b.keys[0]: "Raises bleeding risk.", b.keys[1]: "This is safe."}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    facts = cloud.ask_bucket(b, [topic_for_key(k) for k in b.keys])
    assert [f.key for f in facts] == [b.keys[0]]          # the "safe" answer reads as no_data


def test_live_drops_I7_violations(monkeypatch):
    def handler(request):
        content = json.loads(request.content)["messages"][0]["content"]
        text = "Stop taking it." if content == topic_for_key(_bucket().keys[2]).text else "Known effect."
        return httpx.Response(200, json={"content": [{"type": "text", "text": text}]})
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(handler))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GV_DELAY_S", "0,0")
    b = _bucket()
    facts = cloud.ask_bucket(b, [topic_for_key(k) for k in b.keys])
    assert [f.key for f in facts] == [k for k in b.keys if k != b.keys[2]]


class Counter:
    def __init__(self):
        self.n = 0

    def __call__(self, request):
        self.n += 1
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Known effect."}]})


def test_record_resumes_and_keeps_raw(monkeypatch, tmp_path):
    rec = Counter()
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(rec))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GV_DELAY_S", "0,0")
    buckets = load_buckets()
    b0, b1 = buckets[0], buckets[1]
    (tmp_path / f"{b0.id}.json").write_text(json.dumps({k: "This is safe." for k in b0.keys}))  # complete
    (tmp_path / f"{b1.id}.json").write_text(json.dumps({b1.keys[0]: "partial"}))               # incomplete
    n = cloud.record(tmp_path)
    assert n == 8 * len(buckets)
    assert rec.n == 8 * (len(buckets) - 1)                     # b0 skipped, b1 re-fetched
    assert json.loads((tmp_path / f"{b0.id}.json").read_text())[b0.keys[0]] == "This is safe."  # raw kept
    rec.n = 0
    cloud.record(tmp_path)
    assert rec.n == 0                                           # nothing left to fetch


def test_check_cache_reports_missing_rejected_unknown(tmp_path):
    keys = universe()
    data = {k: "Known effect." for k in keys[2:]}
    data[keys[3]] = "Generally safe."
    data["not|a-key"] = "x"
    (tmp_path / "all.json").write_text(json.dumps(data))
    r = cloud.check_cache(tmp_path)
    assert r["missing"] == keys[:2]
    assert list(r["rejected"]) == [keys[3]]
    assert r["unknown"] == ["not|a-key"]
    assert r["answered"] == len(keys) - 3 and r["universe"] == len(keys)
    assert not r["ok"]


def test_check_cli_exit_codes(tmp_path, capsys):
    (tmp_path / "all.json").write_text(json.dumps({k: "Known effect." for k in universe()}))
    assert cloud._main(["check", str(tmp_path)]) == 0
    assert cloud._main(["check", str(tmp_path / "empty")]) == 1
    assert cloud._main(["nope"]) == 2
    assert "missing" in capsys.readouterr().out
