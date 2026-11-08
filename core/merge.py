"""Merge (Agent C, M9): turn a general Answer plus local flags into an answer about this user.

Runs entirely on device. The Answer from the router is generalized (it never saw the profile); this
module is where it meets the private Profile, so its output is shown on screen and never sent anywhere.

Deterministic on purpose (no model call): the wording rules below are guaranteed by code, and it works
offline in demo mode (I8).

- I4: only flags the rules engine produced are personalized; nothing is inferred between drugs.
- I6: cloud facts are labeled "AI-summarized, verify"; serious wording comes only from flags
  (curated rule tables), never from cloud text.
- I7: never says a drug or combination is s-a-f-e and never tells the user to start or stop anything.
  `guard` enforces this on every string this module returns.

Output is plain text; paragraphs are separated by a blank line.
"""
from __future__ import annotations

import importlib
import importlib.util
import re

from .contracts import Answer, Fact, Flag, Profile

WITHHELD = ("The general answer was withheld because it did not match a keyed source. "
            "Your local flags below still apply.")


def _output_check():
    """B's validator.check_output(text, facts) -> bool, once core/validator.py exists (agreed in
    coord/inbox/to-C/20261108-1345-from-B-g2-interfaces.md). Until then nothing is checked here."""
    if importlib.util.find_spec("core.validator") is None:
        return None
    return getattr(importlib.import_module("core.validator"), "check_output", None)

CLOSING = ("Bring this to your pharmacist or doctor. GenomeVault prepares you for that conversation; "
           "it never tells you to start or stop a medication.")
CLOUD_LABEL = "AI-summarized, verify"

# I7 guard. Whole-sentence removal keeps the remaining text readable and honest.
_BANNED = [
    re.compile(r"\bsafe(r|st|ly)?\b", re.I),
    re.compile(r"\bno (risk|danger)\b", re.I),
    re.compile(r"\b(stop|start|quit|discontinue|resume)\s+(taking|using|your|the|it|this)\b", re.I),
    re.compile(r"\b(discontinue|switch to|switch from)\b", re.I),
    re.compile(r"\byou (should|must|need to) (take|stop|start|switch|avoid)\b", re.I),
    re.compile(r"\b(double|halve|increase|decrease|lower|raise) (your|the) dose\b", re.I),
]
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _violates(sentence: str) -> bool:
    return any(p.search(sentence) for p in _BANNED)


def guard(text: str) -> str:
    """Drop any sentence that calls something s-a-f-e or gives a start/stop/dose instruction (I7)."""
    paragraphs = []
    for para in text.split("\n\n"):
        kept = [s for s in _SENTENCE.split(para.strip()) if s and not _violates(s)]
        if kept:
            paragraphs.append(" ".join(kept))
    return "\n\n".join(paragraphs)


# ---------- describing a flag in the user's own terms (local only) ----------

def _human(s: str) -> str:
    return s.replace("_", " ")


def _key_parts(key: str) -> tuple[list[str], list[str], list[str]]:
    """Split an exact key into (drugs, genes, lab/dose/allergy conditions).
    Allergy keys (A-011) look like `allergy:penicillin|amoxicillin`; the allergen goes to conditions as
    `allergy:<allergen>`, never to genes."""
    drugs, genes, conds = [], [], []
    for part in key.split("|"):
        if part.startswith("allergy:"):
            conds.append(part)
        elif ":" in part:
            genes.append(part.split(":", 1)[0])
        elif re.search(r"[<>]", part):
            conds.append(part)
        else:
            drugs.append(part)
    return drugs, genes, conds


def _lab_trend(profile: Profile, test: str) -> str | None:
    rows = sorted((l for l in profile.labs if l.test.lower() == test.lower()), key=lambda l: l.date)
    if not rows:
        return None
    name = rows[-1].test                     # the profile's spelling ("eGFR"), not the key token ("egfr")
    if len(rows) > 1:
        return f"{name} {rows[-2].value:g} → {rows[-1].value:g} {rows[-1].unit}"
    return f"{name} {rows[-1].value:g} {rows[-1].unit}"


def describe(flag: Flag, profile: Profile) -> str:
    """One sentence tying a flag to this user's genes, doses and labs."""
    drugs, genes, conds = _key_parts(flag.key)
    doses = {d.ingredient: d.dose_mg for d in profile.meds}
    bits = []
    for d in drugs:
        dose = doses.get(d)
        bits.append(f"{_human(d)} {dose:g} mg" if dose is not None else _human(d))
    for g in genes:
        gt = profile.genotypes.get(g)
        ph = profile.phenotypes.get(g)
        if gt and ph:
            bits.append(f"your {g} result {gt} ({_human(ph)})")
        elif ph:
            bits.append(f"your {g} result ({_human(ph)})")
    for c in conds:
        if c.startswith("allergy:"):
            bits.append(f"your {_human(c.split(':', 1)[1])} allergy on record")
            continue
        test = re.split(r"[<>]", c, maxsplit=1)[0]
        if test == "dose":
            continue  # already expressed by the drug dose
        trend = _lab_trend(profile, test)
        if trend:
            bits.append(f"your {trend}")
    # Genes and labs named in the evidence but not in the key
    # (e.g. CYP2C19 behind the omeprazole pair, an eGFR trend behind a potassium rule).
    for g in sorted(profile.phenotypes):
        named = re.compile(rf"\b{re.escape(g)}\b", re.I)
        if g not in genes and any(named.search(e) for e in flag.evidence):
            bits.append(f"your {g} result {profile.genotypes.get(g, '')} ({_human(profile.phenotypes[g])})".replace("  ", " "))
    for lab in sorted({l.test for l in profile.labs}):
        named = re.compile(rf"\b{re.escape(lab)}\b", re.I)
        if not named.search(" ".join(bits)) and any(named.search(e) for e in flag.evidence):
            trend = _lab_trend(profile, lab)
            if trend:
                bits.append(f"your {trend}")
    if not bits:
        joined = flag.key
    elif len(bits) == 1:
        joined = bits[0]
    else:
        joined = ", ".join(bits[:-1]) + " and " + bits[-1]
    return f"{flag.id} ({flag.severity}): {joined}."


def _mentions(flag: Flag, haystack: str) -> bool:
    drugs, genes, _ = _key_parts(flag.key)
    return any(re.search(rf"\b{re.escape(t)}\b", haystack, re.I) for t in drugs + genes)


def relevant_flags(answer: Answer, flags: list[Flag], profile: Profile | None = None) -> list[Flag]:
    """Flags whose drugs or genes the answer (text or fact keys) talks about, plus flags about a drug that
    isn't on the med list: those exist only because the question named that drug (B-025), e.g. X5 for
    "Can I take ibuprofen?", whose local answer text names no drug."""
    haystack = " ".join([answer.text, *(f.key for f in answer.facts), *(f.text for f in answer.facts)])
    on_list = {m.ingredient for m in profile.meds} if profile else None
    order = {"high": 0, "medium": 1, "low": 2}
    hits = [f for f in flags
            if _mentions(f, haystack) or (on_list is not None and any(d not in on_list for d in _key_parts(f.key)[0]))]
    return sorted(hits, key=lambda f: (order[f.severity], f.id, f.key))


# ---------- the answer ----------

def _sources(facts: list[Fact]) -> str:
    names = sorted({f.source for f in facts if f.tier == "curated"})
    return ", ".join(names) if names else "the curated tables"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().rstrip(".").lower()


def _tier_label(fact: Fact) -> str:
    return CLOUD_LABEL if fact.tier == "cloud" else f"Curated ({fact.source})"


def _lead(answer: Answer) -> tuple[str, set[int]]:
    """Opening paragraph, plus the indexes of facts it already states (shown once, not repeated)."""
    if answer.state == "no_data":
        return ("GenomeVault has no data on this, on this device or from a curated source. "
                "A missing entry does not mean there is no interaction."), set()
    if answer.state == "none_listed":
        return (f"No interaction is listed for this in {_sources(answer.facts)}. "
                "That only means the source lists none; it is not a guarantee."), set()
    text = guard(answer.text.strip())
    if not text:
        return "", set()
    # Only the cloud-derived text is checked: the personal part below quotes the user's own doses
    # and labs, which come from the profile, never from facts.
    check = _output_check()
    if check is not None and not check(text, answer.facts):
        return WITHHELD, set()
    # Facts the general text already states: label them here instead of repeating them (I6 kept).
    covered = {i for i, f in enumerate(answer.facts) if _norm(guard(f.text)) and _norm(guard(f.text)) in _norm(text)}
    labels = []
    if answer.sent_to_cloud or any(f.tier == "cloud" for f in answer.facts):
        labels.append(CLOUD_LABEL)
    labels += [_tier_label(answer.facts[i]) for i in sorted(covered) if answer.facts[i].tier == "curated"]
    labels = list(dict.fromkeys(labels))
    return f"In general: {text}" + "".join(f" ({l}.)" for l in labels), covered


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in guard(text).split("\n\n") if p.strip()]


def _fact_order(answer: Answer, flags: list[Flag]) -> list[int]:
    """Lead with what the question brought in. The contract gives merge no question, so: facts whose key
    no local flag already covers come first (Q07: clopidogrel|pantoprazole before the clopidogrel
    background its flags pull in); ties keep the router's order."""
    flag_keys = {f.key for f in flags}
    return sorted(range(len(answer.facts)), key=lambda i: (answer.facts[i].key in flag_keys, i))


def structure(answer: Answer, flags: list[Flag], profile: Profile) -> list[dict]:
    """The merged answer as ordered sections, for a UI that leads with the asked pair and folds the rest.
    Kinds: lead (state line or general text), fact (one keyed fact: key, label, primary, paragraphs),
    personal ("For you" / "Separately"), closing. personalize() flattens exactly this (I6, I7 guarded)."""
    sections: list[dict] = []
    facts = answer.facts
    general = guard(answer.text.strip())
    # Router answers are their facts' texts joined (B-006). Then build the general part fact by fact.
    by_fact = (answer.state == "known" and facts and general
               and all(_norm(guard(f.text)) and _norm(guard(f.text)) in _norm(general) for f in facts))
    if by_fact:
        check = _output_check()
        if check is not None and not check(general, facts):
            sections.append({"kind": "lead", "paragraphs": [WITHHELD]})
        else:
            for n, i in enumerate(_fact_order(answer, flags)):
                f = facts[i]
                paras = _paragraphs(f.text)
                if paras:
                    sections.append({"kind": "fact", "key": f.key, "label": _tier_label(f), "tier": f.tier,
                                     "primary": n == 0, "paragraphs": paras})
    else:
        lead, covered = _lead(answer)
        if lead:
            sections.append({"kind": "lead", "paragraphs": [lead]})
        for i in _fact_order(answer, flags):
            f = facts[i]
            paras = _paragraphs(f.text)
            if paras and i not in covered:
                sections.append({"kind": "fact", "key": f.key, "label": _tier_label(f), "tier": f.tier,
                                 "primary": False, "paragraphs": paras})

    mine = relevant_flags(answer, flags, profile)
    if mine:
        sections.append({"kind": "personal", "paragraphs": ["For you: " + " ".join(describe(f, profile) for f in mine)]})
    else:
        high = list(dict.fromkeys(f.id for f in flags if f.severity == "high"))   # X5 spans 4 keys
        if high:
            ids = high[0] if len(high) == 1 else ", ".join(high[:-1]) + " and " + high[-1]
            sections.append({"kind": "personal", "paragraphs": [
                f"Separately, your flagged item{'' if len(high) == 1 else 's'} {ids} "
                f"{'is' if len(high) == 1 else 'are'} still worth raising."]})
    sections.append({"kind": "closing", "paragraphs": [CLOSING]})
    return sections


def _flatten(sections: list[dict]) -> str:
    out = []
    for sec in sections:
        paras = list(sec["paragraphs"])
        if sec["kind"] == "fact":
            if sec["primary"]:
                paras[0] = f"In general: {paras[0]}"
                paras[-1] = f"{paras[-1]} ({sec['label']}.)"
            else:
                paras[0] = f"{sec['label']}: {paras[0]}"
        out += paras
    return "\n\n".join(p for p in out if p)


def personalize(answer: Answer, flags: list[Flag], profile: Profile) -> str:
    """Contract: merge.personalize(answer, flags, profile) -> str (coord/CONTRACTS.md)."""
    out = guard(_flatten(structure(answer, flags, profile)))
    return out or CLOSING
