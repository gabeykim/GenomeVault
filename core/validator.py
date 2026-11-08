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
Fact. The text is first normalized (NFKC, invisible characters dropped, Cyrillic/Greek look-alikes
mapped, spelled-out "s a f e" / "S.A.F.E." joined). It is rejected if any word contains "safe"
(safe, safely, safety, unsafe); if it reassures without the word (fine, harmless, no risk,
risk-free, nothing to worry, okay to...); if it is not English; or if a sentence tells anyone to
start, stop or change a medicine: an imperative at the start ("Stop taking...", "Consider
switching...", "Keep using..."), a subject plus modal plus such a verb anywhere ("Patients should
stop...", "You could switch..."), or advice phrasing ("it is best to", "I would recommend",
"... is recommended/advisable", "should be stopped"). Rejection is deliberately blunt: a rejected answer is dropped and its key reads as
`no_data` (I4), which is always allowed; a wrongly kept one would break I7.
"""
from __future__ import annotations

import re
import unicodedata
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

# Look-alike letters from other scripts that read as Latin (Cyrillic, Greek). NFKC handles
# full-width and ligatures; Unicode format characters (zero-width, soft hyphen) are dropped.
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "ѕ": "s", "і": "i",
    "ј": "j", "ԁ": "d", "һ": "h", "ӏ": "l", "ԛ": "q", "ԝ": "w", "ɡ": "g", "ɑ": "a",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C",
    "Т": "T", "Х": "X", "Ѕ": "S", "І": "I", "Ј": "J",
    "α": "a", "ο": "o", "ε": "e", "ρ": "p", "ν": "v", "τ": "t", "κ": "k", "ι": "i",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N",
    "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
})
# Three or more single letters split by spaces/dots/dashes ("s a f e", "S.A.F.E.") are joined.
_SPELLED_RE = re.compile(r"(?<![A-Za-z])[A-Za-z](?:[\s.\-_*·]+[A-Za-z](?![A-Za-z])){2,}\.?")


def _normalize(text: str) -> str:
    """Text as a reader sees it: NFKC, no invisible characters, look-alikes mapped, spelled-out
    words joined. Every I7 check runs on this form so character tricks cannot slip through."""
    t = unicodedata.normalize("NFKC", text)
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Cf")
    t = t.translate(_CONFUSABLES)
    return _SPELLED_RE.sub(lambda m: re.sub(r"[^A-Za-z]", "", m.group(0)), t)


_SAFE_RE = re.compile(r"[a-z]*safe[a-z]*", re.I)
_REASSURE_RE = re.compile(
    r"\b(?:fine|harmless|risk[\s-]*free|no\s+risk|without\s+(?:any\s+)?risk|nothing\s+to\s+(?:worry|fear)|"
    r"no\s+(?:need\s+to\s+)?worry|not\s+(?:a\s+)?(?:concern|worry|problem)|no\s+(?:cause\s+for\s+)?concerns?|"
    r"no\s+problems?|ok(?:ay)?\s+to|alright\s+to|all\s+right\s+to|won['’]?t\s+(?:hurt|harm)|not\s+harmful)\b",
    re.I)
_VERBS = (r"(?:stop|start|begin|discontinue|quit|cease|resume|avoid|take|use|switch|change|"
          r"increase|decrease|reduce|lower|raise|double|halve|skip|continue|consider|try|keep|"
          r"hold|pause|cut|add|drop|substitute|replace|taper|wean|go\s+ahead)")
_VERB_END = r"\b(?![-'’])"                                                   # not "Take-home"
_NOUN_USE = r"(?!\s+(?:of|in|on|is|was|were|are|may|can|has|had|with)\b)"   # "Use of...", "Increase in..."
_IMPERATIVE_RE = re.compile(
    rf"^\W*(?:(?:do\s+not|don['’]t|never|please|just)\s+)?{_VERBS}{_VERB_END}{_NOUN_USE}", re.I)
_SUBJECT = (r"(?:you|you['’]ll|you['’]d|patients?|people|persons?|users?|adults?|one|they|we|he|she|"
            r"the\s+patient|the\s+reader|anyone|everyone|someone)")
_MODAL = (r"(?:should|must|need\s+to|needs\s+to|have\s+to|has\s+to|can|could|may|might|ought\s+to|"
          r"will|would|(?:may|might|will|would)?\s*(?:want|wish)\s+to|are\s+(?:advised|encouraged|told)\s+to|"
          r"is\s+(?:advised|encouraged|told)\s+to|had\s+better|better)")
_SUBJECT_MODAL_RE = re.compile(
    rf"\b{_SUBJECT}\s+{_MODAL}\s+(?:not\s+|never\s+|just\s+|safely\s+)?(?:keep\s+|go\s+ahead\s+and\s+)?"
    rf"{_VERBS}{_VERB_END}", re.I)
_ADVICE_RE = re.compile(
    r"\b(?:it\s+is|it['’]s|it\s+would\s+be|it\s+may\s+be|it\s+might\s+be)\s+(?:best|better|wise|advisable|"
    r"recommended|prudent|sensible|a\s+good\s+idea)\s+to\b|"
    r"\b(?:i|we)\s+(?:would\s+|strongly\s+)?(?:recommend|suggest|advise|urge)\b|"
    r"\b(?:is|are|be)\s+(?:strongly\s+)?(?:recommended|advised|advisable|suggested|preferred|warranted)\b|"
    r"\bshould\s+be\s+(?:stopped|started|discontinued|avoided|switched|changed|reduced|increased|"
    r"lowered|halved|doubled|continued|resumed|taken|used|held|paused|skipped|replaced|tapered)\b",
    re.I)

# Non-English answers are rejected: the I7 checks only understand English (D-008 red team).
_FOREIGN = frozenset((
    "es el la los las con del y que para por una tomar seguro segura sin pero muy está "      # es
    "le les avec est pour et une des sans sûr très "                                          # fr
    "und mit ist nicht der die das sicher ein eine kein oder "                                # de
    "com é não uma sem "                                                                      # pt
    "il è sicuro non della".split()))                                                         # it
_EN = frozenset("the a an is are was were of and to in on with for this that it be may can not or "
                "by as at from these those its their your has have".split())


def _language_problem(t: str) -> str | None:
    letters = [ch for ch in t if ch.isalpha()]
    if letters:
        other = [ch for ch in letters if not unicodedata.name(ch, "").startswith("LATIN") and ch != "μ"]
        if len(other) > 0.2 * len(letters):
            return "not English (non-Latin script)"
    words = re.findall(r"[^\W\d_]+", t.lower())
    foreign = sum(w in _FOREIGN for w in words)
    if foreign >= 2 and foreign > sum(w in _EN for w in words):
        return "not English"
    return None


def wording_problems(text: str) -> list[str]:
    """Every I7 problem in `text` ('says "safe"', 'reassures', 'instruction: ...', 'not English').
    Empty means acceptable. Checks run on the normalized text (see `_normalize`)."""
    t = _normalize(text)
    out = [f'says "{m.group(0)}"' for m in _SAFE_RE.finditer(t)]
    out += [f'reassures: "{m.group(0)}"' for m in _REASSURE_RE.finditer(t)]
    lang = _language_problem(t)
    if lang:
        out.append(lang)
    for sentence in _SENT_SPLIT.split(t):
        s = sentence.strip()
        if _IMPERATIVE_RE.search(s) or _SUBJECT_MODAL_RE.search(s) or _ADVICE_RE.search(s):
            out.append(f"instruction: {s[:80]!r}")
    return out


def check_wording(text: str) -> bool:
    """True if `text` never says "safe" and gives no start/stop/change instruction (I7)."""
    return not wording_problems(text)
