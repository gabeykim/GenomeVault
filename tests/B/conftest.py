import pytest

from core import cloud, router


@pytest.fixture(autouse=True)
def _no_real_sleep_no_cover(monkeypatch):
    """B tests never really sleep (P6.4 delays are asserted through the injected sleep) and never
    leave a cover thread running (P6.6)."""
    monkeypatch.setattr(cloud, "_sleep", lambda s: None)
    yield
    router.stop_cover()
