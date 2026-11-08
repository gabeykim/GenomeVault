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

Answer state (I4, missing = no_data): `known` if at least one asked key has a fact, or if a local flag
covers the question (it shares a drug the question names, or the question names none) and no key that
the cloud or the partition could answer is left open. Anything else is `no_data`: a question no flag
covers is never "checked, nothing found". The question's own subject is parsed locally
(`_subject_keys`): named drug pairs, gene-drug keys when it mentions genes, drug-lab keys when it names a
lab test. (`none_listed` needs a curated "no interaction" entry from A's tables via the KB.)
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
from .decoys import aliases_of, bucket_for, load_aliases, load_buckets, universe
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


def _vocab() -> set[str]:
    vocab: set[str] = set()
    for k in universe():
        vocab |= _key_drugs(k)
    return vocab


def _normalized(question: str) -> set[str]:
    """Ingredient ids A's normalizer reads in the question: brand and typed names ("Plavix",
    "Advil"), multi-word names (local only, never sent)."""
    try:
        from .normalize import to_ingredients
        return {d.ingredient.strip().lower() for d in to_ingredients(question)}
    except Exception:  # the plain word match below still works
        return set()


def _named_drugs(question: str) -> list[str]:
    """Drugs of the bucket universe the user names in the question (local parse, never sent).
    A brand name counts as its ingredient (I4: "Plavix with Protonix" asks clopidogrel|pantoprazole)."""
    vocab = _vocab()
    words = set(_WORD_RE.findall(question.lower())) | _normalized(question)
    return sorted(w for w in words if w in vocab)


def _question_keys(question: str) -> list[str]:
    """Exact drug-drug keys for pairs of known drugs the user names in the question (local parse)."""
    named = _named_drugs(question)
    return [pair_key(a, b) for i, a in enumerate(named) for b in named[i + 1:]]


# Words that put a gene or a lab test in the question's subject (local parse only).
_GENE_WORDS = {"gene", "genes", "genetic", "genetics", "genotype", "genotypes", "genome", "dna", "pgx"}
_LAB_WORDS = {
    "ck": "ck", "cpk": "ck", "kinase": "ck",
    "alt": "alt", "liver": "alt",
    "egfr": "egfr", "kidney": "egfr", "kidneys": "egfr", "renal": "egfr",
    "potassium": "potassium", "sodium": "sodium", "magnesium": "magnesium",
    "glucose": "glucose", "sugar": "glucose", "inr": "inr", "tsh": "tsh", "thyroid": "tsh",
}
_LAB_PART_RE = re.compile(r"^([a-z0-9]+)\s*[<>]")


def _key_gene(key: str) -> Optional[str]:
    head = key.split("|", 1)[0]
    return head.split(":", 1)[0].upper() if ":" in head else None


def _key_lab(key: str) -> Optional[str]:
    for part in key.lower().split("|"):
        m = _LAB_PART_RE.match(part.strip())
        if m and not part.strip().startswith("dose"):
            return m.group(1)
    return None


def _subject_keys(question: str, flags: list[Flag], profile: Optional[Profile]) -> tuple[list[str], list[str]]:
    """The exact keys the question itself asks about, and the drugs it names (I4).

    - pairs of named drugs (`_question_keys`);
    - gene-drug keys of the partition for a named drug, when the question mentions genes and the gene is
      assessed in the profile (the topic sent covers every phenotype, P6.3);
    - drug-lab keys of the partition when the question names a lab test, for the named drugs, or for the
      drugs of the caller's flags when it names none ("my liver tests and my statin").
    A gene-drug or drug-lab key is skipped when a flag already covers that same gene or lab for that drug:
    the flag carries the person's own phenotype or band.
    """
    named = _named_drugs(question)
    keys = _question_keys(question)
    words = set(_WORD_RE.findall(question.lower()))
    flag_drugs: set[str] = set()
    for f in flags:
        flag_drugs |= _key_drugs(f.key)
    covered = {(_key_gene(f.key) or _key_lab(f.key), d) for f in flags for d in _key_drugs(f.key)}
    space = list(universe()) + list(load_aliases())
    if profile is not None and named:
        assessed = {g.upper() for g, v in profile.genotypes.items() if v and v != "not_assessed"}
        genes_named = bool(words & _GENE_WORDS) or bool({w.upper() for w in words} & assessed)
        if genes_named:
            for k in space:
                g = _key_gene(k)
                if g in assessed and any(d in named and (g, d) not in covered for d in _key_drugs(k)):
                    keys.append(k)
    labs = {_LAB_WORDS[w] for w in words if w in _LAB_WORDS}
    lab_drugs = set(named) or flag_drugs
    if labs and lab_drugs:
        for k in space:
            lab = _key_lab(k)
            if lab in labs and _key_gene(k) is None and any(d in lab_drugs and (lab, d) not in covered
                                                            for d in _key_drugs(k)):
                keys.append(k)
    return list(dict.fromkeys(keys)), named


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
    # A variant of a member's topic (other phenotype / dose band, decoys.load_aliases) gets the member's
    # answer under its own key: the text asked covers every variant, and nothing extra is sent (I3, I5).
    facts = facts + [f.model_copy(update={"key": a}) for f in facts for a in aliases_of(f.key)]
    return facts, ledger.record(kind, bucket_id=bucket.id, texts=texts)


def route(question: str, flags: list[Flag]) -> Answer:
    today = date.today()
    me = _profile()
    asked, named = _subject_keys(question, flags, me)

    # P6.1 / I4: a flag answers the question only when it covers it: it shares a drug the question
    # names, or the question names no drug at all (the flags are then the caller's context).
    def covers(f: Flag) -> bool:
        return not named or bool(_key_drugs(f.key) & set(named))

    # Only a covering flag's key is looked up: a question about simvastatin must not fetch (or, before
    # a pack sync, send) the clopidogrel buckets, nor answer with their text (I4).
    wanted: list[str] = []
    for f in flags:
        if f.needs_cloud and covers(f) and generalize(f):
            wanted.append(f.key)
    flag_keys = {f.key for f in flags}
    asked = [k for k in asked if k not in flag_keys]
    for k in asked:
        if k not in wanted:
            wanted.append(k)
    flag_covers = any(covers(f) for f in flags)
    # A flag that asks the cloud, or an asked key the partition can answer, left unanswered keeps the
    # answer at no_data (I4). Asked keys outside the partition are never sent and do not hold it back.
    open_keys = [k for k in wanted if k not in asked or bucket_for(k) is not None]

    if not wanted:  # P6.1: nothing to look up
        ledger.record("local_only")
        if flag_covers:
            return Answer(state="known", text=LOCAL_TEXT, facts=[], sent_to_cloud=False)
        return Answer(state="no_data", text=NO_DATA_TEXT, facts=[], sent_to_cloud=False)

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
    profile = me
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
        if flag_covers and not any(k not in found for k in open_keys):
            return Answer(state="known", text=LOCAL_TEXT, facts=[], sent_to_cloud=sent)
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


# Stretch: bulk knowledge-pack sync (F6, F8, E4) ------------------------------------------------

def sync_pack(skip_fresh: bool = True, today: Optional[date] = None) -> dict:
    """Fetch the whole fixed partition into the KB while online, so later questions (and offline
    ones, F8) are answered on-device with 0 bytes.

    Privacy: the set of buckets is the entire partition, the same for every user, and the order is
    shuffled; nothing about a question, flag or profile chooses what is sent (I5). Each bucket goes
    through the normal leakage check (I3) and is logged as a `cover` entry, since it is
    query-independent traffic. With `skip_fresh`, a bucket whose 8 keys are all fresh in the KB is
    not re-sent; the KB only holds answers of buckets already sent whole (or same-for-everyone
    curated facts), so skipping reveals nothing new.

    Returns counts: `sent`, `blocked`, `skipped`, `facts` stored, and `offline` (True if the cloud
    was or became unreachable; the remaining buckets are not tried)."""
    today = today or date.today()
    out = {"sent": 0, "blocked": 0, "skipped": 0, "facts": 0, "offline": False}
    if cloud.offline():
        out["offline"] = True
        return out
    buckets = list(load_buckets())
    _cover_rng.shuffle(buckets)
    profile = _profile()
    for b in buckets:
        if skip_fresh and all(kb.get(k, today) is not None for k in b.keys):
            out["skipped"] += 1
            continue
        try:
            facts, entry = _send_bucket(b.id, profile, kind="cover")
        except _Offline:
            out["offline"] = True
            break
        if entry.kind == "blocked":
            out["blocked"] += 1
            continue
        out["sent"] += 1
        out["facts"] += kb.put_many(facts)
    return out
