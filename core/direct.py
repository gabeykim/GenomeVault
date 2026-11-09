"""Answer-first lead line (GV_DIRECT, D-040 follow-up). Integrator-owned. Entirely on device.

`direct_line(question, answer, flags, profile) -> str | None` composes one short lead that answers the
question as asked, restating ONLY what the flags, facts and answer state already say (I4): which items to
raise with a clinician, which drug to ask about first, what a named drug is flagged against, or the
listed / none-listed / no-data state of a pair. It never says yes or no to "can I take", never gives
start/stop/switch advice and never says the s-word (I7): every line passes `merge.guard` and
`validator.wording_problems` before it is returned, else None. Nothing here touches the network (I3).

`app.py` (GV_DIRECT=1) prepends the line as a `lead` section with `direct: True`, replacing the empty
local lead ("In general: This was checked on your device...") when that is all the router said.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from . import intent, merge
from .contracts import Answer, Flag, Profile
from .validator import wording_problems

_EFFICACY_RE = re.compile(r"\b(help|helps|helping|work|works|working|relieve|relieves|cure|cures|treat|treats|"
                          r"good for|effective)\b")
_CLINICIAN_RE = re.compile(r"\b(cardiologist|pharmacist|doctor|physician|nurse|prescriber|gp|clinician|specialist|"
                           r"nephrologist|neurologist)\b")
_ASK_RE = re.compile(r"\b(ask|bring up|raise|tell|discuss|mention|talk|questions?|follow-up|visit)\b")
_SEV = {"high": 0, "medium": 1, "low": 2}


def enabled() -> bool:
    return os.environ.get("GV_DIRECT", "").strip() == "1"


def _words(question: str) -> list[str]:
    words, _ = intent._normalize_words(question)
    words, _ = intent._repair_words(words, intent._drug_spans(question))
    return words


def _drugs(question: str, words: list[str]) -> list[str]:
    return intent._find_drugs(words, intent._drug_spans(question))


def _join(items: list[str]) -> str:
    items = [i.replace("_", " ") for i in items]
    if not items:
        return ""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _count(n: int) -> str:
    return {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}.get(n, str(n))


def _flag_items(flags: list[Flag], profile: Profile) -> list[str]:
    seen, out = set(), []
    for f in sorted(flags, key=lambda f: (_SEV[f.severity], f.id, f.key)):
        if f.id in seen:        # X5 spans several keys: one line per flag id
            continue
        seen.add(f.id)
        d = merge.describe(f, profile)              # "X1 (high): clopidogrel 75 mg and your CYP2C19 ..."
        body = d.split(": ", 1)[1].rstrip(".") if ": " in d else d.rstrip(".")
        out.append(f"{body} ({f.id}, {f.severity})")
    return out


def _flagged_against(drug: str, flags: list[Flag], profile: Profile) -> list[str]:
    """What `drug` is flagged against in the user's own flags: the partner drugs, genes and lab trends."""
    items: list[str] = []
    for f in flags:
        drugs, genes, conds = merge._key_parts(f.key)
        if drug not in drugs:
            continue
        for d in drugs:
            if d != drug and d.replace("_", " ") not in items:
                items.append(d.replace("_", " "))
        for g in genes:
            s = f"your {g} result"
            if s not in items:
                items.append(s)
        for c in conds:
            test = re.split(r"[<>]", c, maxsplit=1)[0]
            if test == "dose" or c.startswith("allergy:"):
                continue
            trend = merge._lab_trend(profile, test)
            s = f"your {trend}" if trend else f"your {test}"
            if s not in items:
                items.append(s)
    return items


def _pair_state(a: str, b: str, answer: Answer, flags: list[Flag]) -> str:
    """Listed / none listed / no data for the exact pair, from the answer's facts and the user's flags only."""
    from .contracts import pair_key
    key = pair_key(a, b)
    fact = next((f for f in answer.facts if f.key == key), None)
    if fact is not None:
        if answer.state == "none_listed":
            return f"no interaction is listed between {a} and {b} in {fact.source}; that is not a guarantee"
        label = "curated" if fact.tier == "curated" else "AI-summarized; verify"
        return f"an entry is listed for {a} with {b} ({label})"
    if any(f.key == key for f in flags):
        return f"an interaction is flagged between {a} and {b} in your records"
    return f"GenomeVault has no data on {a} with {b}"


def _compose(question: str, answer: Answer, flags: list[Flag], profile: Profile) -> Optional[str]:
    words = _words(question)
    ws = set(words)
    drugs = _drugs(question, words)
    kind, _ = intent._rule_intent(words, drugs)
    low = " ".join(words)

    # 1. what to raise with a clinician
    if not drugs and _CLINICIAN_RE.search(low) and (_ASK_RE.search(low) or kind in {"cardio", "pharm", "followup"}):
        who = _CLINICIAN_RE.search(low).group(1)
        if kind == "pharm" and ("first" in ws or "which" in ws):
            return _which_first(flags, who)
        items = _flag_items([f for f in flags if f.severity in {"high", "medium"}], profile)
        if not items:
            return f"Nothing in your records is flagged right now, so there is no GenomeVault item to raise with your {who}."
        lines = [f"{_count(len(items))} thing{'s' if len(items) != 1 else ''} to raise with your {who}:"]
        lines += [f"{i}. {it}." for i, it in enumerate(items, 1)]
        return "\n".join(lines)
    if kind == "followup" and not drugs:
        items = _flag_items([f for f in flags if f.severity in {"high", "medium"}], profile)
        if items:
            return "\n".join([f"{_count(len(items))} thing{'s' if len(items) != 1 else ''} to raise at your follow-up:"]
                             + [f"{i}. {it}." for i, it in enumerate(items, 1)])

    # 5. pair or substitution
    if kind == "sub" and len(drugs) >= 2:
        new, old = intent._sub_order(words, drugs)
        partners = intent._context_drugs(old, new, flags) or [d for d in drugs if d not in (new, old)]
        if partners:
            p = partners[0]
            return (f"For {p.replace('_', ' ')}, {_pair_state(p, old, answer, flags)}; "
                    f"for {new.replace('_', ' ')}, {_pair_state(p, new, answer, flags)}.").replace("; for", "; for")
        return f"Short answer: {_pair_state(new, old, answer, flags)}."
    if kind == "pair" and len(drugs) >= 2:
        return f"Short answer: {_pair_state(drugs[0], drugs[1], answer, flags)}."

    # 3 / 4. a single named drug: "can I take X", "is X ok", "does X help a headache"
    if len(drugs) == 1 and kind in {"otc", "rx", None} or (len(drugs) == 1 and _EFFICACY_RE.search(low)):
        d = drugs[0]
        name = d.replace("_", " ")
        found = _flagged_against(d, flags, profile)
        if _EFFICACY_RE.search(low):
            head = ("GenomeVault does not answer whether a medicine works for a symptom; that is a question "
                    "for your pharmacist or doctor.")
        else:
            head = (f"GenomeVault does not answer whether to take {name}; that is a question for your "
                    "pharmacist or doctor.")
        if found:
            tail = (f"What it found: {name} is flagged against {_count(len(found)).lower()} "
                    f"thing{'s' if len(found) != 1 else ''} in your records: {_join(found)}.")
        else:
            has_fact = any(d in merge._key_parts(f.key)[0] for f in answer.facts)
            state = ("an entry is listed for it" if has_fact and answer.state == "known"
                     else "no interaction is listed for it; that is not a guarantee" if answer.state == "none_listed"
                     else "GenomeVault has no entry for it with your medications")
            tail = f"Nothing in your records is flagged with {name}, and {state}."
        return f"{head} {tail}"
    return None


def _which_first(flags: list[Flag], who: str) -> str:
    highs = [f for f in flags if f.severity == "high"]
    counts: dict[str, list[str]] = {}
    for f in highs:
        for d in merge._key_parts(f.key)[0]:
            counts.setdefault(d, [])
            if f.id not in counts[d]:
                counts[d].append(f.id)
    if not counts:
        return f"Nothing in your records is flagged high right now, so GenomeVault has no first item for your {who}."
    drug, ids = sorted(counts.items(), key=lambda kv: (-len(kv[1]), sorted(kv[1])[0], kv[0]))[0]
    n = len(ids)
    return (f"Start with {drug.replace('_', ' ')}: it appears in {n} of your high-priority flag{'s' if n != 1 else ''} "
            f"({', '.join(sorted(ids))}).")


def direct_line(question: str, answer: Answer, flags: list[Flag], profile: Profile) -> Optional[str]:
    try:
        line = _compose(question, answer, flags, profile)
    except Exception:          # a lead line is a nicety; the normal answer must never break
        return None
    if not line:
        return None
    for part in line.split("\n"):   # every line (the heading and each numbered item) must survive the guard
        if merge.guard(part).strip() != part.strip() or wording_problems(part):
            return None
    return line


def apply(sections: list[dict], text: str, line: str) -> tuple[list[dict], str]:
    """Put `line` first. The empty local lead (router.LOCAL_TEXT) is replaced; anything else is kept below."""
    from .router import LOCAL_TEXT
    lead = {"kind": "lead", "direct": True, "paragraphs": line.split("\n")}   # heading + numbered items
    out = []
    for s in sections:
        if s.get("kind") == "lead" and any(LOCAL_TEXT in p for p in s.get("paragraphs", [])):
            continue
        out.append(s)
    paras = [p for p in text.split("\n\n") if LOCAL_TEXT not in p]
    return [lead] + out, "\n\n".join(line.split("\n") + paras)
