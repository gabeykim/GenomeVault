"""tests/I run with the D-040 flags pinned: the suite must pass whether or not a developer has
GV_INTENT / GV_DIRECT / GV_FUZZY / GV_TAIL / GV_DEMO_LIVE_FALLBACK exported. Each test sets what it needs."""
import pytest

FLAGS = ("GV_INTENT", "GV_DIRECT", "GV_INTENT_LLM", "GV_FUZZY", "GV_TAIL", "GV_DEMO_LIVE_FALLBACK")


@pytest.fixture(autouse=True)
def _pin_flags(monkeypatch):
    for f in FLAGS:
        monkeypatch.delenv(f, raising=False)
    yield
