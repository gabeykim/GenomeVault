"""The committed knowledge pack in `mocks/cloud_cache/` (D-027) matches partition v5 and fills the KB.

Skips until the pack is on main (PR #6). Uses the real cache dir, not a temp copy.
"""
import json
import os
import pathlib

import pytest

from core import cloud, kb, ledger, router
from core.decoys import load_aliases, load_buckets
from core.validator import wording_problems

# GV_PACK_CHECK points the test at another pack (e.g. one extracted from an unmerged branch).
CACHE = pathlib.Path(os.environ.get("GV_PACK_CHECK", str(cloud.DEFAULT_CACHE)))
FILES = sorted(CACHE.glob("*.json")) if CACHE.is_dir() else []
pytestmark = pytest.mark.skipif(not FILES, reason="mocks/cloud_cache/ not on this branch yet (PR #6, D-027)")


def _pack() -> dict[str, dict[str, str]]:
    return {f.stem: json.loads(f.read_text()) for f in FILES}


@pytest.fixture
def demo(monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DELAY_S",
              "GV_COVER_INTERVAL_S"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_transport", None)
    monkeypatch.setattr(cloud, "_last_failure", None)
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(CACHE))
    ledger.reset()
    kb.reset()
    yield
    cloud.set_offline(None)
    ledger.reset()
    kb.reset()


def test_one_file_per_v5_bucket_with_exactly_its_keys():
    pack = _pack()
    buckets = {b.id: set(b.keys) for b in load_buckets()}
    assert set(pack) == set(buckets)
    for bid, answers in pack.items():
        assert set(answers) == buckets[bid], bid


def test_every_recorded_answer_passes_wording_check_i7():
    bad = {k: wording_problems(t) for a in _pack().values() for k, t in a.items() if wording_problems(t)}
    assert bad == {}
    assert all(t.strip() for a in _pack().values() for t in a.values())


def test_sync_from_committed_pack_fills_kb(demo):
    buckets = load_buckets()
    r = router.sync_pack()
    assert r == {"sent": len(buckets), "blocked": 0, "skipped": 0,
                 "facts": 8 * len(buckets) + len(load_aliases()), "offline": False}
    assert all(e.kind == "cover" and e.personal_fields_sent == 0 for e in ledger.feed(0))
