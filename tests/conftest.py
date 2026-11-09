"""Integrator: the two integrator flags (GV_INTENT, GV_DIRECT) are unset for every test unless a test sets
them itself, so the suite gives the same result whether or not a developer has them exported. Other
agents' flags (GV_FUZZY, GV_TAIL, ...) are left to their own tests."""
import pytest


@pytest.fixture(autouse=True)
def _integrator_flags_off(monkeypatch):
    for f in ("GV_INTENT", "GV_DIRECT", "GV_INTENT_LLM"):
        monkeypatch.delenv(f, raising=False)
    yield
