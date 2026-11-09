"""D-041: the real router.single_candidates / send_single keep the CONTRACTS signatures and, with
GV_TAIL off, behave exactly like the flag-off stubs in core/interfaces.py (nothing sent, no ledger row)."""
import inspect
import typing

import pytest

from core import interfaces, kb, ledger, router
from core.contracts import pair_key


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DEMO_LIVE_FALLBACK",
              "GV_TAIL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(router.cloud, "_forced", None)
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


@pytest.mark.parametrize("name", ["single_candidates", "send_single"])
def test_signature_matches_interfaces_stub(name):
    real, stub = getattr(router, name), getattr(interfaces, name)
    assert list(inspect.signature(real).parameters) == list(inspect.signature(stub).parameters)
    assert typing.get_type_hints(real) == typing.get_type_hints(stub)


@pytest.mark.parametrize("q", ["can I take x with y?", "can I take amoxicillin with my warfarin?",
                               "is ibuprofen ok with my sertraline?"])
def test_single_candidates_flag_off_is_stub(q):
    assert router.single_candidates(q, []) == interfaces.single_candidates(q, []) == []


@pytest.mark.parametrize("key", ["x|y", pair_key("amoxicillin", "warfarin"), pair_key("ibuprofen", "sertraline")])
def test_send_single_flag_off_is_stub(key):
    real, stub = router.send_single(key), interfaces.send_single(key)
    assert (real.state, real.sent_to_cloud, real.facts) == (stub.state, stub.sent_to_cloud, stub.facts)
    assert ledger.feed() == []
