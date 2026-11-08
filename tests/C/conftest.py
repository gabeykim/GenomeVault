"""Isolation for C's tests once B's real router, ledger and KB are merged.

- Demo mode, no API key, empty cloud cache: /api/ask can never make a live cloud call from a test,
  and results don't depend on whatever is in mocks/cloud_cache/.
- No persistence paths, and a fresh ledger and KB per test (B's advice in
  coord/inbox/to-C/20261108-1430-from-B-kb-ready.md), so repeat questions don't turn into KB hits.
"""
import importlib
import importlib.util

import pytest


def _reset(module: str) -> None:
    if importlib.util.find_spec(f"core.{module}") is not None:
        mod = importlib.import_module(f"core.{module}")
        if hasattr(mod, "reset"):
            mod.reset()


@pytest.fixture(autouse=True)
def offline_demo(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path / "empty-cloud-cache"))
    monkeypatch.delenv("GV_KB_PATH", raising=False)
    monkeypatch.delenv("GV_LEDGER_PATH", raising=False)
    _reset("ledger")
    _reset("kb")
    yield
