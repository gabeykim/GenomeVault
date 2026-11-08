"""Queue 9 / F8 / E4: offline mode answers from P6 steps 1-2 only and sends nothing."""
import json

import httpx
import pytest

from core import cloud, kb, ledger, router
from core.contracts import Flag
from core.decoys import bucket_for

X1 = Flag(id="X1", key="CYP2C19:poor_metabolizer|clopidogrel", severity="high", engine="gene_drug",
          evidence=["CYP2C19 poor metabolizer"], needs_cloud=True)
X3 = Flag(id="X3", key="SLCO1B1:decreased_function|simvastatin|dose>20mg", severity="medium",
          engine="gene_drug", evidence=["simvastatin 40 mg"], needs_cloud=False)


def _flag(key):
    return Flag(id="Y", key=key, severity="low", engine="gene_drug", evidence=[], needs_cloud=True)


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_last_failure", None)

    def boom(request):
        raise AssertionError("offline mode touched the network")
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(boom))
    b = bucket_for(X1.key)
    (tmp_path / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


def test_env_switch_forces_offline_even_in_demo(monkeypatch):
    monkeypatch.setenv("GV_OFFLINE", "1")
    assert cloud.offline()
    assert cloud.status() == {"online": False, "demo": True, "forced_offline": True}
    b = bucket_for(X1.key)
    with pytest.raises(cloud.CloudUnavailable):
        cloud.ask_bucket(b, [router.topic_for_key(b.keys[0])])


def test_runtime_switch_overrides_env(monkeypatch):
    monkeypatch.setenv("GV_OFFLINE", "1")
    cloud.set_offline(False)
    assert not cloud.offline()
    cloud.set_offline(None)
    assert cloud.offline()


def test_offline_cold_kb_is_no_data_zero_bytes_no_ledger():
    cloud.set_offline(True)
    a = router.route("clopidogrel?", [X1])
    assert a.state == "no_data" and not a.sent_to_cloud
    assert a.text == router.OFFLINE_TEXT
    assert ledger.feed(0) == []


def test_offline_warm_kb_still_answers():
    router.route("clopidogrel?", [X1])          # online: bucket sent, all 8 stored
    ledger.reset()
    cloud.set_offline(True)
    a = router.route("clopidogrel?", [X1])
    assert a.state == "known" and not a.sent_to_cloud
    assert [e.kind for e in ledger.feed(0)] == ["kb_hit"]


def test_offline_decoy_key_learned_earlier_is_answered():
    b = bucket_for(X1.key)
    router.route("clopidogrel?", [X1])
    cloud.set_offline(True)
    decoy = next(k for k in b.keys if k != X1.key)
    assert router.route("?", [_flag(decoy)]).state == "known"


def test_offline_local_rules_still_work():
    cloud.set_offline(True)
    a = router.route("Is my simvastatin dose a problem?", [X3])
    assert a.state == "known" and [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_network_failure_stops_after_first_bucket_and_reports_offline(monkeypatch):
    calls = []

    def down(request):
        calls.append(request)
        raise httpx.ConnectError("down", request=request)
    monkeypatch.delenv("DEMO")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(cloud, "_transport", httpx.MockTransport(down))
    other = next(k for k in router.universe() if bucket_for(k).id != bucket_for(X1.key).id)
    a = router.route("?", [X1, _flag(other)])
    assert a.state == "no_data" and a.text == router.OFFLINE_TEXT and not a.sent_to_cloud
    assert len(calls) == 1                              # second bucket never tried
    assert ledger.feed(0) == []
    assert cloud.status()["online"] is False


def test_status_never_sends(monkeypatch):
    monkeypatch.delenv("DEMO")
    assert cloud.status() == {"online": False, "demo": False, "forced_offline": False}   # no key
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert cloud.status()["online"] is True


def test_kb_clear_wipes_file(tmp_path, monkeypatch):
    path = tmp_path / "kb.json"
    monkeypatch.setenv("GV_KB_PATH", str(path))
    kb.reset()
    router.route("clopidogrel?", [X1])
    assert path.exists() and kb.get(X1.key) is not None
    kb.clear()
    assert not path.exists() and kb.get(X1.key) is None
    kb.reset()
    assert kb.get(X1.key) is None
