"""Privacy router (F4, M5): decides what leaves the device. Implements PLAN P6 steps 1-5, 7, 8.

`route(question, flags) -> Answer` (contract: router.route).

1. Local rules: the caller (A's rules) already produced `flags`. Only flags with `needs_cloud`
   (and never allergy flags) ask for general knowledge. If none does, nothing is sent.
2. KB: an exact-key fact that has not expired answers the key; nothing is sent (`kb_hit`).
3. Generalize: each remaining key becomes one Topic phrased for all phenotypes / lab bands.
4. Split: one Topic per request, one session per bucket (cloud.py). Random delays are queue 8.
5. Bucket: the key's fixed bucket of 8 (I5) is sent whole, and all 8 answers are kept.
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

import re
from datetime import date
from typing import Optional

from . import cloud, kb, ledger
from .contracts import Answer, Fact, Flag, Profile, Topic, pair_key
from .decoys import bucket_for, universe
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


def _send_bucket(bucket_id: str, profile: Profile) -> tuple[list[Fact], bool]:
    """Send one whole fixed bucket. Returns (facts, sent). Blocked sends return no facts; raises
    _Offline if the cloud is unreachable (nothing left the device, no ledger entry)."""
    from .decoys import load_buckets

    bucket = next(b for b in load_buckets() if b.id == bucket_id)
    topics: list[Topic] = [topic_for_key(k) for k in bucket.keys]
    texts = [t.text for t in topics]
    allow: set[str] = set()
    for k in bucket.keys:
        allow |= _key_drugs(k)
    if any(leaks(t, profile, allow) for t in texts):
        ledger.record("blocked", bucket_id=bucket.id)
        return [], False
    try:
        facts = cloud.ask_bucket(bucket, topics)
    except cloud.CloudUnavailable as e:
        raise _Offline() from e
    ledger.record("bucket", bucket_id=bucket.id, texts=texts)
    return facts, True


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
            facts, ok = _send_bucket(b.id, profile)
        except _Offline:
            is_offline = True
            break
        sent = sent or ok
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
