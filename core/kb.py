"""Learning knowledge base (F6, M6, P6.2): exact-key facts with trust tier and expiry.

`get(key) -> Fact | None` (contract: kb.get). The router stores every answer of a sent bucket here,
decoys included (P6.5), so a repeat question, or a later question about any of the 7 decoy keys, is
answered on-device with 0 bytes out.

Rules enforced here:
- Exact key only (I4). No normalization, no prefix or similarity match: a missing key is a miss.
- Expired facts are never returned (I6: cloud facts expire sooner; cloud.py sets their expiry).
- A `curated` fact is never replaced by a `cloud` fact for the same key (I6), even if the curated
  one has expired: an expired curated fact is a miss, and a fresh cloud answer is served for it
  only after the curated fact is removed. A newer fact of the same tier replaces the old one.

Persistence: in memory by default. If `GV_KB_PATH` is set, the store is a JSON file at that path,
loaded on first use and rewritten on every put, so the KB survives an app restart (S6: "it learns").
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
from datetime import date
from typing import Iterable, Optional

from .contracts import Fact

_lock = threading.Lock()
_facts: dict[str, Fact] = {}
_loaded = False


def _path() -> Optional[pathlib.Path]:
    p = os.environ.get("GV_KB_PATH")
    return pathlib.Path(p) if p else None


def _load_locked() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    p = _path()
    if not p or not p.exists():
        return
    for row in json.loads(p.read_text() or "[]"):
        f = Fact.model_validate(row)
        _facts[f.key] = f


def _save_locked() -> None:
    p = _path()
    if not p:
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps([f.model_dump(mode="json") for f in _facts.values()], indent=1))
    tmp.replace(p)


def _keep_old(old: Fact, new: Fact) -> bool:
    if old.tier == "curated" and new.tier == "cloud":
        return True
    return new.tier == old.tier and new.fetched < old.fetched


def get(key: str, today: Optional[date] = None) -> Optional[Fact]:
    """The unexpired fact stored under exactly `key`, else None."""
    today = today or date.today()
    with _lock:
        _load_locked()
        f = _facts.get(key)
    return f if f is not None and f.expires >= today else None


def put(fact: Fact) -> bool:
    """Store one fact. Returns False if an existing fact outranks it (curated over cloud, newer over older)."""
    return put_many([fact]) == 1


def put_many(facts: Iterable[Fact]) -> int:
    """Store several facts with one write. Returns how many were stored."""
    n = 0
    with _lock:
        _load_locked()
        for f in facts:
            old = _facts.get(f.key)
            if old is not None and _keep_old(old, f):
                continue
            _facts[f.key] = f
            n += 1
        if n:
            _save_locked()
    return n


def remove(key: str) -> bool:
    with _lock:
        _load_locked()
        hit = _facts.pop(key, None) is not None
        if hit:
            _save_locked()
    return hit


def all_facts() -> list[Fact]:
    with _lock:
        _load_locked()
        return sorted(_facts.values(), key=lambda f: f.key)


def stats(today: Optional[date] = None) -> dict[str, int]:
    """Counts for the UI / E2 learning curve: total, fresh, expired, and fresh by tier."""
    today = today or date.today()
    out = {"total": 0, "fresh": 0, "expired": 0, "curated": 0, "cloud": 0}
    for f in all_facts():
        out["total"] += 1
        if f.expires >= today:
            out["fresh"] += 1
            out[f.tier] += 1
        else:
            out["expired"] += 1
    return out


def reset() -> None:
    """Forget the in-memory store and reload from `GV_KB_PATH` on next use (tests, demo reset)."""
    global _loaded
    with _lock:
        _facts.clear()
        _loaded = False


def clear() -> None:
    """Empty the KB, including the `GV_KB_PATH` file (cold runs for E2/E4, demo reset)."""
    global _loaded
    with _lock:
        _facts.clear()
        _loaded = True
        p = _path()
        if p and p.exists():
            p.unlink()
