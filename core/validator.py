"""Validator: outbound leakage check (I3, P6.7) and answer output check (I4).

Outbound (`leaks`, `check_outbound`): runs on every text just before it leaves the device. If it
finds anything, the router turns the send into a `blocked` ledger entry with 0 bytes out.
A text is blocked if it contains:
- any standalone number (a run of digits not glued to a letter, e.g. "48", "5.2", "75mg",
  "*2/*2", "2026-10-28"). Generalized Topics carry no numbers at all, so this catches every
  dose, lab value, date, age and genotype without needing to know them. Digits inside a word
  (gene symbols such as CYP2C19, SLCO1B1) are allowed.
- a star allele (`*2`), whatever the profile holds.
- any profile value: genotype, phenotype (as `poor_metabolizer` or `poor metabolizer`),
  condition, allergy, or a med's dose; matched case-insensitively on word boundaries.
`allow` lists terms that may appear even though they are profile values. The router passes the
drug ingredients of the fixed bucket being sent: those are the public content of the bucket (I5)
and every member of the bucket names its own drugs.

Output (`check_output`): True only if every drug pair and every number in an answer text comes
from one of the keyed Facts behind it (I4: no extrapolation). Drugs are recognised from the
bucket universe plus the drugs named in the facts' keys. A pair is two drugs named in the same
sentence; it is covered when one fact names both drugs (in its key or its text). A number is
covered when it appears as a number in a fact's text or key.

Wording (`wording_problems`, `check_wording`): I7 on every cloud answer before it can become a
Fact. A text is rejected if any word contains "safe" (safe, safely, safety, unsafe), or if a
sentence tells the reader to start, stop or change a medicine: an imperative at the start of a
sentence ("Stop taking...", "Do not take...", "Avoid...") or "you should/must/need to/can" followed
by such a verb. Rejection is deliberately blunt: a rejected answer is dropped and its key reads as
`no_data` (I4), which is always allowed; a wrongly kept one would break I7.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

from .contracts import Fact, Profile

_NUM_RE = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?")
_STAR_RE = re.compile(r"\*\s*\d")
_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")
_WORD_RE = re.compile(r"[a-z][a-z0-9-]*")


def _norm_num(s: str) -> str:
    """'40', '40.0' and '40.00' are the same number."""
    try:
        return f"{float(s):g}"
    except ValueError:
        return s


def numbers_in(text: str) -> list[str]:
    """Standalone numbers in `text` (digits inside a word, like CYP2C19, are not numbers)."""
    return [_norm_num(m.group(0)) for m in _NUM_RE.finditer(text)]


def _term_re(term: str) -> re.Pattern:
    spaced = re.escape(term.replace("_", " ")).replace(r"\ ", r"[\s_-]+")
    return re.compile(rf"(?<![A-Za-z0-9]){spaced}(?![A-Za-z0-9])", re.IGNORECASE)


def _profile_terms(profile: Profile) -> list[tuple[str, str]]:
    """(field, value) pairs that must never appear in outbound text."""
    terms: list[tuple[str, str]] = []
    for gene, gt in profile.genotypes.items():
        terms.append((f"genotype:{gene}", gt))
    for gene, ph in profile.phenotypes.items():
        terms.append((f"phenotype:{gene}", ph))
    terms += [("condition", c) for c in profile.conditions]
    terms += [("allergy", a) for a in profile.allergies]
    return [(f, v) for f, v in terms if v and v.strip()]


def leaks(text: str, profile: Profile, allow: Iterable[str] = ()) -> list[str]:
    """Every personal field found in an outbound text, as 'field: value'. Empty means safe (I3)."""
    allowed = {a.lower() for a in allow}
    found: list[str] = []
    for n in numbers_in(text):
        found.append(f"number: {n}")
    if _STAR_RE.search(text):
        found.append("star_allele")
    for field, value in _profile_terms(profile):
        if value.lower() in allowed:
            continue
        if _term_re(value).search(text):
            found.append(f"{field}: {value}")
    return found


def check_outbound(texts: Iterable[str], profile: Profile, allow: Iterable[str] = ()) -> bool:
    """True only if no text leaks a personal field. The router blocks the send on False."""
    allow = list(allow)
    return all(not leaks(t, profile, allow) for t in texts)


# ---------------------------------------------------------------- output check (I4)

def _key_drugs(key: str) -> set[str]:
    """Drug ingredient tokens in an exact key (drops gene:phenotype, lab bands, dose bands)."""
    out = set()
    for part in key.lower().split("|"):
        part = part.strip()
        if not part or ":" in part or part.startswith("dose") or re.search(r"[<>]", part):
            continue
        if _WORD_RE.fullmatch(part):
            out.add(part)
    return out


@lru_cache(maxsize=1)
def _universe_drugs() -> frozenset[str]:
    try:
        from .decoys import universe
        keys = universe()
    except Exception:  # bucket file missing: fall back to facts' own drugs
        keys = []
    drugs: set[str] = set()
    for k in keys:
        drugs |= _key_drugs(k)
    return frozenset(drugs)


def _drugs_in(text: str, vocab: Iterable[str]) -> set[str]:
    words = set(_WORD_RE.findall(text.lower()))
    return {d for d in vocab if d in words}


def check_output(text: str, facts: list[Fact]) -> bool:
    """True only if every drug pair and every number in `text` comes from one of `facts` (I4)."""
    fact_nums: set[str] = set()
    covers: list[set[str]] = []
    vocab = set(_universe_drugs())
    for f in facts:
        vocab |= _key_drugs(f.key)
    for f in facts:
        fact_nums.update(numbers_in(f.text))
        fact_nums.update(numbers_in(f.key))
        covers.append(_key_drugs(f.key) | _drugs_in(f.text, vocab))

    if any(n not in fact_nums for n in numbers_in(text)):
        return False

    for sentence in _SENT_SPLIT.split(text):
        drugs = sorted(_drugs_in(sentence, vocab))
        for i, a in enumerate(drugs):
            for b in drugs[i + 1:]:
                if not any(a in c and b in c for c in covers):
                    return False
    return True


# ---------------------------------------------------------------- wording check (I7)

_SAFE_RE = re.compile(r"[a-z]*safe[a-z]*", re.I)
_VERBS = (r"(?:stop|start|begin|discontinue|quit|cease|resume|avoid|take|use|switch|change|"
          r"increase|decrease|reduce|lower|raise|double|halve|skip|continue)")
_NOUN_USE = r"(?!\s+(?:of|in|on|is|was|were|are|may|can|has|had|with)\b)"   # "Use of...", "Increase in..."
_IMPERATIVE_RE = re.compile(rf"^\W*(?:(?:do\s+not|don['’]t|never|please)\s+)?{_VERBS}\b{_NOUN_USE}", re.I)
_YOU_SHOULD_RE = re.compile(
    rf"\byou\s+(?:should|must|need\s+to|have\s+to|can|may\s+want\s+to|ought\s+to)\s+(?:not\s+)?{_VERBS}\b", re.I)


def wording_problems(text: str) -> list[str]:
    """Every I7 problem in `text` ('says "safe"', 'instruction: ...'). Empty means acceptable."""
    out = [f'says "{m.group(0)}"' for m in _SAFE_RE.finditer(text)]
    for sentence in _SENT_SPLIT.split(text):
        s = sentence.strip()
        m = _IMPERATIVE_RE.search(s) or _YOU_SHOULD_RE.search(s)
        if m:
            out.append(f"instruction: {s[:80]!r}")
    return out


def check_wording(text: str) -> bool:
    """True if `text` never says "safe" and gives no start/stop/change instruction (I7)."""
    return not wording_problems(text)
