import pytest

from core import cloud, router

# macOS Finder/iCloud leaves untracked copies like "test_cloud 2.py" in the worktree. They are never
# committed, but pytest collects them and double-counts B's tests locally. Skip them.
collect_ignore_glob = ["* [0-9].py", "* [0-9][0-9].py"]


@pytest.fixture(autouse=True)
def _no_real_sleep_no_cover(monkeypatch):
    """B tests never really sleep (P6.4 delays are asserted through the injected sleep) and never
    leave a cover thread running (P6.6)."""
    monkeypatch.setattr(cloud, "_sleep", lambda s: None)
    yield
    router.stop_cover()
