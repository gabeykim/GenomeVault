"""Privacy router (F4, M5): decides what leaves the device. Implements PLAN P6 steps 1-8.

`route(question, flags) -> Answer` (contract: router.route).

1. Local rules: the caller (A's rules) already produced `flags`. Only flags with `needs_cloud`
   (and never allergy flags) ask for general knowledge. If none does, nothing is sent.
2. KB: an exact-key fact that has not expired answers the key; nothing is sent (`kb_hit`).
3. Generalize: each remaining key becomes one Topic phrased for all phenotypes / lab bands.
4. Split: one Topic per request, one session per bucket, a random pause before every request
   (cloud.py, `GV_DELAY_S`).
5. Bucket: the key's fixed bucket of 8 (I5) is sent whole, and all 8 answers are kept.
6. Cover traffic: `send_cover()` sends one bucket drawn uniformly from the whole fixed partition,
   chosen without looking at any question, KB or flag (I5). `start_cover()` runs it on a steady,
   jittered schedule (every `GV_COVER_INTERVAL_S` seconds, default 60, times a random 0.5-1.5) in a
   daemon thread; the app starts it, `stop_cover()` ends it. Cover sends go through the same
   leakage check and ledger (kind `cover`), and their 8 answers are stored in the KB like any other.
   Nothing is sent while offline.
7. Leakage check (I3) on every outbound text. Any hit blocks the whole bucket: 0 bytes leave.
8. One ledger entry per decision: `local_only`, `kb_hit`, `bucket` or `blocked`.

The question text itself never leaves the device. It is read locally only, to find drug pairs the
user names directly (e.g. "clopidogrel and pantoprazole") so they can be answered by exact key.
A key outside the bucket universe is never sent and gets no fact (I4/I5: `no_data`).

Offline (F8): when cloud.offline() is forced, steps 3-8 are skipped entirely: no generalizing, no
ledger entry, 0 bytes. KB and local answers still work; anything else is `no_data` with OFFLINE_TEXT.
If a send fails mid-question (network down), the remaining buckets are not tried.

Answer state: `known` if at least one asked key has a fact, else `no_data`. (`none_listed` needs
a curated "no interaction" entry, which comes from A's curated tables via the KB.)
"""
from __future__ import annotations

import os
import random
import re
import threading
from datetime import date
from typing import Optional

from . import cloud, kb, ledger
from .contracts import Answer, Fact, Flag, LedgerEntry, Profile, Topic, pair_key
from .decoys import bucket_for, load_buckets, universe
from .generalize import generalize, topic_for_key
from .validator import _key_drugs, leaks

_WORD_RE = re.compile(r"[a-z][a-z0-9-]*")

NO_DATA_TEXT = ("No entry was found for this exact question. A missing entry does not mean there "
                "is no interaction; ask your pharmacist.")
OFFLINE_TEXT = ("You are offline, and this exact question is not stored on your device yet. Nothing "
                "was sent. A missing entry does not mean there is no interaction; ask your pharmacist.")
LOCAL_TEXT = "This was checked on your device against your own records. Nothing was sent."


def _profile() -> Profile:
    """The on-device profile, for the leakage check only. A's real loader once it exists."""
    try:
        from .graph import load_profile  # type: ignore
    except ImportError:
        from .interfaces import load_profile
    return load_profile()


def _question_keys(question: str) -> list[str]:
    """Exact drug-drug keys for pairs of known drugs the user names in the question (local parse)."""
    vocab: set[str] = set()
    keys = set(universe())
    for k in keys:
        vocab |= _key_drugs(k)
    named = sorted({w for w in _WORD_RE.findall(question.lower()) if w in vocab})
    return [pair_key(a, b) for i, a in enumerate(named) for b in named[i + 1:]]


def _kb_get(key: str, today: date) -> Optional[Fact]:
    return kb.get(key, today)


def _kb_put(facts: list[Fact]) -> None:
    kb.put_many(facts)


class _Offline(Exception):
    pass


def _send_bucket(bucket_id: str, profile: Profile, kind: str = "bucket") -> tuple[list[Fact], LedgerEntry]:
    """Send one whole fixed bucket (`kind` "bucket" or "cover"). Returns (facts, ledger entry). Blocked
    sends return no facts and a `blocked` entry; raises _Offline if the cloud is unreachable (nothing left, no ledger entry)."""
    bucket = next(b for b in load_buckets() if b.id == bucket_id)
    topics: list[Topic] = [topic_for_key(k) for k in bucket.keys]
    texts = [t.text for t in topics]
    allow: set[str] = set()
    for k in bucket.keys:
        allow |= _key_drugs(k)
    if any(leaks(t, profile, allow) for t in texts):
        return [], ledger.record("blocked", bucket_id=bucket.id)
    try:
        facts = cloud.ask_bucket(bucket, topics)
    except cloud.CloudUnavailable as e:
        raise _Offline() from e
    return facts, ledger.record(kind, bucket_id=bucket.id, texts=texts)


def route(question: str, flags: list[Flag]) -> Answer:
    today = date.today()
    wanted: list[str] = []
    for f in flags:
        if f.needs_cloud and generalize(f):
            wanted.append(f.key)
    for k in _question_keys(question):
        if k not in wanted:
            wanted.append(k)

    if not wanted:  # P6.1: local rules answer it
        ledger.record("local_only")
        return Answer(state="known", text=LOCAL_TEXT, facts=[], sent_to_cloud=False)

    found: dict[str, Fact] = {}
    missing: list[str] = []
    for k in wanted:  # P6.2
        f = _kb_get(k, today)
        if f is not None:
            found[k] = f
        else:
            missing.append(k)
    if found:
        ledger.record("kb_hit")

    is_offline = bool(missing) and cloud.offline()
    if is_offline:  # F8: steps 1-2 only
        missing = []
    profile = _profile() if missing else None
    sent = False
    done: set[str] = set()
    for k in missing:  # P6.3-5, 7, 8
        b = bucket_for(k)
        if b is None or b.id in done:
            continue
        done.add(b.id)
        try:
            facts, entry = _send_bucket(b.id, profile)
        except _Offline:
            is_offline = True
            break
        sent = sent or entry.kind != "blocked"
        _kb_put(facts)  # store all 8 answers
        for f in facts:
            if f.key in missing:
                found[f.key] = f

    facts = [found[k] for k in wanted if k in found]
    if not facts:
        text = OFFLINE_TEXT if is_offline else NO_DATA_TEXT
        return Answer(state="no_data", text=text, facts=[], sent_to_cloud=sent)
    text = "\n\n".join(f.text for f in facts)
    return Answer(state="known", text=text, facts=facts, sent_to_cloud=sent)



# P6.6 cover traffic ---------------------------------------------------------------------------

_cover_rng = random.SystemRandom()
_cover_thread: Optional[threading.Thread] = None
_cover_stop = threading.Event()
DEFAULT_COVER_INTERVAL_S = 60.0


def send_cover() -> Optional[LedgerEntry]:
    """Send one cover bucket, drawn uniformly from the fixed partition (never from a query, I5).
    Returns its ledger entry (`cover`, or `blocked` if the leakage check stopped it), or None when
    nothing was attempted (offline, or the cloud is unreachable)."""
    if cloud.offline():
        return None
    b = _cover_rng.choice(load_buckets())
    try:
        facts, entry = _send_bucket(b.id, _profile(), kind="cover")
    except _Offline:
        return None
    _kb_put(facts)
    return entry


def cover_interval() -> float:
    v = float(os.environ.get("GV_COVER_INTERVAL_S", DEFAULT_COVER_INTERVAL_S))
    if v <= 0:
        raise ValueError("GV_COVER_INTERVAL_S must be > 0")
    return v


def _cover_loop(interval: float, stop: threading.Event) -> None:
    while not stop.wait(interval * _cover_rng.uniform(0.5, 1.5)):
        try:
            send_cover()
        except Exception:   # cover traffic must never take the app down; the next tick retries
            pass


def start_cover(interval_s: Optional[float] = None) -> bool:
    """Start steady cover traffic in a daemon thread. Returns False if it is already running."""
    global _cover_thread, _cover_stop
    if cover_running():
        return False
    interval = interval_s if interval_s is not None else cover_interval()
    if interval <= 0:
        raise ValueError("cover interval must be > 0")
    _cover_stop = threading.Event()
    _cover_thread = threading.Thread(target=_cover_loop, args=(interval, _cover_stop),
                                     name="gv-cover", daemon=True)
    _cover_thread.start()
    return True


def stop_cover(timeout: float = 5.0) -> None:
    global _cover_thread
    _cover_stop.set()
    if _cover_thread is not None:
        _cover_thread.join(timeout)
    _cover_thread = None


def cover_running() -> bool:
    return _cover_thread is not None and _cover_thread.is_alive()
