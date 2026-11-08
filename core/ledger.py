"""Ledger of everything that leaves the device (F5, M7, P6.8).

The router writes one entry per decision: `bucket` / `cover` sends, and the zero-byte outcomes
`kb_hit`, `local_only` and `blocked`. The UI polls `feed(since)` (cheap: a slice of an in-memory list).

Rules enforced here, so a buggy caller cannot write a misleading ledger:
- `seq` starts at 1 and strictly increases.
- Only `bucket` and `cover` entries may have `bytes_out > 0`; the rest record that nothing left.
- `bucket` and `cover` entries must name a `bucket_id`.
- `personal_fields_sent` must stay 0 (I3). A send with personal fields is never recorded as sent:
  the leakage check turns it into a `blocked` entry with 0 bytes out.

The exact outbound texts of each send are kept on-device (`outbound(seq)`) so the UI can show what
left (S4). They are generalized Topic texts only, never the user's question.

Persistence: in memory by default. If `GV_LEDGER_PATH` is set, entries are appended to that JSONL
file and reloaded on first use, so the ledger survives an app restart.
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
from datetime import datetime, timezone
from typing import Optional

from .contracts import LedgerEntry

SENDING_KINDS = {"bucket", "cover"}
KINDS = {"bucket", "cover", "kb_hit", "local_only", "blocked"}

_lock = threading.Lock()
_entries: list[LedgerEntry] = []
_texts: dict[int, list[str]] = {}
_loaded = False


def _path() -> Optional[pathlib.Path]:
    p = os.environ.get("GV_LEDGER_PATH")
    return pathlib.Path(p) if p else None


def _load_locked() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    p = _path()
    if not p or not p.exists():
        return
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        texts = row.pop("texts", [])
        e = LedgerEntry.model_validate(row)
        _entries.append(e)
        _texts[e.seq] = texts


def bytes_of(texts: list[str]) -> int:
    """Outbound size: UTF-8 bytes of every text sent."""
    return sum(len(t.encode("utf-8")) for t in texts)


def record(
    kind: str,
    bucket_id: Optional[str] = None,
    texts: Optional[list[str]] = None,
    personal_fields_sent: int = 0,
) -> LedgerEntry:
    """Append one entry. `texts` are the exact strings sent (only for `bucket` / `cover`)."""
    texts = list(texts or [])
    if kind not in KINDS:
        raise ValueError(f"unknown ledger kind {kind!r}")
    if personal_fields_sent != 0:
        raise ValueError("personal_fields_sent must be 0; block the send instead (I3)")
    if kind in SENDING_KINDS:
        if not bucket_id:
            raise ValueError(f"{kind} entry needs a bucket_id")
        if not texts:
            raise ValueError(f"{kind} entry needs the outbound texts")
    elif texts:
        raise ValueError(f"{kind} entry sends nothing; texts must be empty")

    with _lock:
        _load_locked()
        seq = _entries[-1].seq + 1 if _entries else 1
        e = LedgerEntry(
            seq=seq,
            ts=datetime.now(timezone.utc),
            bucket_id=bucket_id,
            kind=kind,
            bytes_out=bytes_of(texts),
            personal_fields_sent=0,
        )
        _entries.append(e)
        _texts[seq] = texts
        p = _path()
        if p:
            p.parent.mkdir(parents=True, exist_ok=True)
            row = json.loads(e.model_dump_json())
            row["texts"] = texts
            with p.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return e


def feed(since: int = 0) -> list[LedgerEntry]:
    """Entries with `seq > since`, oldest first (contract: ledger.feed)."""
    with _lock:
        _load_locked()
        if since <= 0:
            return list(_entries)
        # seq increases along the list: walk back from the end, so polling for new entries is O(new)
        i = len(_entries)
        while i > 0 and _entries[i - 1].seq > since:
            i -= 1
        return list(_entries[i:])


def outbound(seq: int) -> list[str]:
    """The exact texts sent in entry `seq` (empty for zero-byte entries or unknown seq)."""
    with _lock:
        _load_locked()
        return list(_texts.get(seq, []))


def totals() -> dict:
    """Running totals for the UI: bytes out, sends, and count per kind."""
    with _lock:
        _load_locked()
        by_kind = {k: 0 for k in sorted(KINDS)}
        for e in _entries:
            by_kind[e.kind] += 1
        return {
            "entries": len(_entries),
            "bytes_out": sum(e.bytes_out for e in _entries),
            "personal_fields_sent": sum(e.personal_fields_sent for e in _entries),
            "by_kind": by_kind,
        }


def reset() -> None:
    """Clear the ledger (tests, demo restart), including the JSONL file if `GV_LEDGER_PATH` is set."""
    global _loaded
    with _lock:
        _entries.clear()
        _texts.clear()
        _loaded = True
        p = _path()
        if p and p.exists():
            p.unlink()
