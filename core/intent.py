"""Question understanding (D-040 adaptive questions), on-device only. Integrator-owned.

`canonicalize(question, flags) -> Understanding` rewrites a free-form question (paraphrase, synonym,
word order, typo) into the canonical wording of a question the system already answers, so that
`router.route()` sees the same text it sees for the scripted question. Only `app.py`'s `/api/ask`
calls it, only with `GV_INTENT=1`, and only *before* `route()`: the rewrite goes through every
privacy step unchanged (generalize, fixed buckets of 8, cover, leakage check, ledger).

Privacy and invariants:
- Everything here is string processing on the device (stdlib only). Nothing is sent anywhere, no
  network module is imported, and no new field about the question is persisted (I3).
- A paraphrase can only map to an intent the system already answers, with the drugs the user
  actually named in its slots; nothing is ever inferred into a different drug (I4). Drug-name typos
  are repaired only when A's `normalize.suggest` (GV_FUZZY) returns a single unambiguous
  `assumed` name; look-alikes are never substituted. Ordinary-word typos ("cardiolgist") are
  repaired against the closed vocabulary of the canonical questions.
- When the intent is not clear the ORIGINAL question is routed unchanged (today's behaviour) and
  `clarify` offers the closest canonical phrasings for the UI to show; nothing is guessed silently.
- Optional last resort, `GV_INTENT_LLM=1` only: the local model (core.local_llm, localhost Ollama)
  picks ONE intent id from the closed list or "none"; the choice is validated against the list and
  can never add facts, drugs or text.

Layers, cheapest first: normalize (lowercase, punctuation, contractions, synonym table in
data/intent/synonyms.json) -> word typo repair (difflib) -> slotting (drug / lab / gene / role
words) -> deterministic cue rules -> token-set similarity -> optional local LLM.
"""
from __future__ import annotations

import difflib
import functools
import json
import os
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

from .contracts import Flag

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "intent"
QUERIES = pathlib.Path(__file__).resolve().parent.parent / "eval" / "queries.json"

_WORD_RE = re.compile(r"[a-z][a-z0-9'-]*|\d+(?:\.\d+)?")
_CONTRACTIONS = {
    "i'm": "i am", "im": "i am", "i've": "i have", "ive": "i have", "i'd": "i would", "i'll": "i will",
    "it's": "it is", "that's": "that is", "what's": "what is", "whats": "what is", "isn't": "is not",
    "don't": "do not", "dont": "do not", "doesn't": "does not", "doesnt": "does not", "can't": "can not",
    "cant": "can not", "couldn't": "could not", "won't": "will not", "should've": "should have",
    "u": "you", "ur": "your", "pls": "please", "plz": "please", "w/": "with", "w": "with", "&": "and",
    "+": "and", "ok": "okay", "ok?": "okay",
}
# Lab and gene cue words the router reads (router._LAB_WORDS / _GENE_WORDS); kept here as slots.
_LAB_WORDS = {"ck", "cpk", "kinase", "alt", "liver", "egfr", "kidney", "kidneys", "renal", "potassium",
              "sodium", "magnesium", "glucose", "sugar", "inr", "tsh", "thyroid"}
_GENE_WORDS = {"gene", "genes", "genetic", "genetics", "genotype", "genotypes", "genome", "dna", "pgx"}
_SUB_CUES = {"instead", "swap", "swapped", "swapping", "trade", "trading", "switch", "switching", "switched",
             "replace", "replacing", "substitute", "alternative", "vs", "versus", "rather"}
_INTERACT_CUES = {"interact", "interaction", "interactions", "together", "with", "and", "problem", "issue",
                  "combine", "mix", "mixing", "same"}
_TAKE_CUES = {"take", "taking", "use", "using", "have", "okay", "fine", "alright", "can", "could", "should"}
_RX_CUES = {"prescribed", "prescription", "started", "starting", "new", "put"}
# Questions about another person, or asking for start/stop/dose-change advice (I7), are never
# rewritten into one of the canonical questions: the original goes through unchanged.
_GUARD = {"dog", "cat", "pet", "wife", "husband", "son", "daughter", "kid", "kids", "child", "children", "baby",
          "friend", "mom", "mother", "dad", "father", "brother", "sister", "grandma", "grandpa", "partner",
          "stop", "stopping", "quit", "quitting", "double", "doubling", "increase", "increasing", "decrease",
          "lower", "lowering", "halve", "skip", "skipping", "overdose", "buy", "order", "price", "cost",
          "ancestry", "weather", "joke", "export", "download", "appointment", "who", "drink", "alcohol", "wine", "beer"}
_STOP = {"i", "my", "me", "a", "an", "the", "is", "it", "to", "of", "for", "with", "and", "or", "do", "does",
         "did", "be", "am", "are", "was", "were", "that", "this", "if", "ever", "just", "any", "some", "at",
         "in", "on", "about", "would", "could", "should", "can", "will", "there", "anything", "something",
         "mg", "you", "your", "they", "them", "given", "since", "last", "year", "today", "might", "may",
         "please", "hi", "hey", "so", "ok", "okay", "not"}


@dataclass
class Intent:
    id: str                      # canonical question id (eval/queries.json), e.g. "Q07"
    kind: str                    # cue family: sub / pair / lab / gene / otc / rx / cardio / pharm / followup
    canonical: str               # the scripted wording
    tokens: set[str] = field(default_factory=set)


@dataclass
class Understanding:
    question: str                         # what to route (canonical rewrite or the original)
    rewritten: bool = False
    intent_id: Optional[str] = None
    understood_as: Optional[str] = None   # UI: "I took this as: ..."
    clarify: list[str] = field(default_factory=list)   # UI: "Did you mean one of these?"
    confidence: float = 0.0
    repairs: list[tuple[str, str]] = field(default_factory=list)   # (typed, repaired) word pairs
    drugs: list[str] = field(default_factory=list)


def enabled() -> bool:
    return os.environ.get("GV_INTENT", "").strip() == "1"


# data ------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _synonyms() -> tuple[list[tuple[tuple[str, ...], tuple[str, ...]]], dict[str, str]]:
    """Phrase synonyms (longest first) and single-word synonyms from data/intent/synonyms.json."""
    raw = json.loads((DATA / "synonyms.json").read_text())
    phrases = []
    words = {}
    for src, dst in raw["phrases"].items():
        s, d = tuple(src.split()), tuple(dst.split())
        if len(s) > 1:
            phrases.append((s, d))
        else:
            words[s[0]] = dst
    phrases.sort(key=lambda p: -len(p[0]))
    return phrases, words


_KIND_OF = {"Q01": "rx", "Q02": "gene", "Q03": "gene", "Q04": "gene", "Q05": "gene", "Q06": "pair", "Q07": "sub",
            "Q08": "pair", "Q09": "pair", "Q10": "pair", "Q11": "lab", "Q12": "lab", "Q13": "lab", "Q14": "lab",
            "Q15": "otc", "Q16": "otc", "Q17": "sub", "Q18": "cardio", "Q19": "pharm", "Q20": "followup"}


@functools.lru_cache(maxsize=1)
def intents() -> list[Intent]:
    qs = json.loads(QUERIES.read_text())["queries"]
    out = []
    for q in qs:
        it = Intent(id=q["id"], kind=_KIND_OF.get(q["id"], "other"), canonical=q["text"])
        it.tokens = _content_tokens(_slot(_normalize_words(q["text"])[0]))
        out.append(it)
    return out


@functools.lru_cache(maxsize=1)
def _vocab() -> set[str]:
    """Closed vocabulary for ordinary-word typo repair: words of the canonical questions and the synonym
    table, plus the router's cue words. Drug names are deliberately NOT in it (I4)."""
    v: set[str] = set()
    for q in json.loads(QUERIES.read_text())["queries"]:
        v |= set(_WORD_RE.findall(q["text"].lower()))
    phrases, words = _synonyms()
    for s, d in phrases:
        v |= set(s) | set(d)
    for s, d in words.items():
        v.add(s); v |= set(d.split())
    v |= _LAB_WORDS | _GENE_WORDS | _SUB_CUES | _INTERACT_CUES | _TAKE_CUES | _RX_CUES | _STOP
    v |= {"what", "which", "how", "when", "where", "why", "who", "ask", "tell", "know", "need", "matter",
          "concern", "level", "result", "test", "tests", "dose", "doses", "work", "works", "affect", "better",
          "headache", "pain", "anxiety", "medications", "medication", "medicine", "meds", "prescriptions",
          "follow-up", "followup", "function", "pressure", "blood", "bring", "up", "first", "raise", "discuss",
          "mention", "questions", "visit", "next", "dropped", "worse", "came", "back", "reading", "added",
          "add", "makes", "make", "sense", "procedure", "mentioned", "doctor", "doc", "put", "got", "still",
          "worth", "important", "aware", "safe", "fit", "fits", "right", "change", "changing", "from"}
    v = {w for w in v if w}
    try:   # drug names out (I4): a misspelled drug is never "repaired" here, only by normalize.suggest
        from .normalize import to_ingredients
        v = {w for w in v if not to_ingredients(w)}
    except Exception:
        pass
    return v


# layer a: normalization ----------------------------------------------------------------------------

def _drug_spans(text: str) -> dict[str, str]:
    """word-sequence -> ingredient id, for drug names A's normalizer reads in the text (local only).
    Windows of 1-3 words are tried longest first ("st johns wort", "advil")."""
    try:
        from .normalize import to_ingredients
    except Exception:
        return {}
    words = [w.strip("'-") for w in _WORD_RE.findall(text.lower().replace("’", "'"))]
    words = [w for w in words if w]
    found: dict[str, str] = {}
    i = 0
    while i < len(words):
        hit = None
        for n in (3, 2, 1):
            win = words[i:i + n]
            if len(win) < n or any(w in _STOP or w in _SUB_CUES for w in win):
                continue
            try:
                ds = to_ingredients(" ".join(win))
            except Exception:
                ds = []
            if len(ds) == 1:
                hit = (n, ds[0].ingredient.strip().lower())
                break
        if hit:
            found[" ".join(words[i:i + hit[0]])] = hit[1]
            found[hit[1]] = hit[1]
            i += hit[0]
        else:
            i += 1
    return found


def _normalize_words(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Lowercase, punctuation out, contractions expanded, phrase and word synonyms applied.
    Returns the word list and the (typed, replaced) synonym substitutions applied."""
    t = text.lower().replace("’", "'").replace("/", " ").replace("+", " and ").replace("&", " and ")
    t = re.sub(r"(\d)\s*mg\b", r"\1 mg", t)
    words = []
    for w in _WORD_RE.findall(t):
        w = w.strip("'-")
        if not w:
            continue
        words.extend(_CONTRACTIONS.get(w, w).split())
    phrases, singles = _synonyms()
    out: list[str] = []
    subs: list[tuple[str, str]] = []
    i = 0
    while i < len(words):
        hit = None
        for src, dst in phrases:
            if tuple(words[i:i + len(src)]) == src:
                hit = (src, dst)
                break
        if hit:
            out.extend(hit[1]); subs.append((" ".join(hit[0]), " ".join(hit[1]))); i += len(hit[0])
            continue
        w = words[i]
        if w in singles:
            out.extend(singles[w].split())
            if singles[w] != w:
                subs.append((w, singles[w]))
        else:
            out.append(w)
        i += 1
    return out, subs


# layer b: typo repair -------------------------------------------------------------------------------

def _is_drug_word(w: str, drugs: dict[str, str]) -> bool:
    if w in drugs:
        return True
    return any(w in k.split() for k in drugs)


def _repair_words(words: list[str], drugs: dict[str, str]) -> tuple[list[str], list[tuple[str, str]]]:
    """Ordinary-word typos against the closed vocabulary (edit distance <= 2, length-aware). Words that
    are drug names, numbers, or already in the vocabulary are left alone. Unknown words that are not
    close to anything stay as typed (never guessed)."""
    vocab = _vocab()
    out, fixes = [], []
    for w in words:
        if w in vocab or w.isdigit() or _is_drug_word(w, drugs) or len(w) < 4:
            out.append(w)
            continue
        cutoff = 0.84 if len(w) >= 6 else 0.8 if len(w) >= 4 else 0.75
        near = difflib.get_close_matches(w, vocab, n=2, cutoff=cutoff)
        if near and _edits(w, near[0]) <= 2:
            out.append(near[0]); fixes.append((w, near[0]))
        else:
            out.append(w)
    return out, fixes


def _edits(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _repair_drugs(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Drug-name typos via A's normalize.suggest (GV_FUZZY, PR #17) when present: only an unambiguous
    `assumed` suggestion is applied; `ask` (look-alikes, several choices) is left for the UI. Without
    suggest(), drug names are left exactly as typed (I4)."""
    try:
        from . import normalize
    except Exception:
        return text, []
    suggest = getattr(normalize, "suggest", None)
    if suggest is None:
        return text, []
    try:
        items = suggest(text)
    except Exception:
        return text, []
    fixes = []
    for it in sorted(items, key=lambda d: -d["span"][0]):
        if it.get("mode") == "assumed" and it.get("assumed") and len(it.get("choices", [])) == 1:
            s, e = it["span"]
            fixes.append((text[s:e], it["assumed"]))
            text = text[:s] + it["assumed"] + text[e:]
    return text, fixes


# layer c: slots, cue rules, similarity -------------------------------------------------------------

def _slot(words: list[str]) -> list[str]:
    out = []
    for w in words:
        if w in _LAB_WORDS:
            out.append("<lab>")
        elif w in _GENE_WORDS:
            out.append("<gene>")
        else:
            out.append(w)
    return out


def _content_tokens(words: list[str]) -> set[str]:
    return {w for w in words if w not in _STOP and not w.isdigit()}


def _find_drugs(words: list[str], drugs: dict[str, str]) -> list[str]:
    """Ingredient ids in the order the user named them (brand -> ingredient via A's table)."""
    text = " ".join(words)
    hits: list[tuple[int, str]] = []
    for src, ing in drugs.items():
        pat = r"\b" + re.escape(src) + r"\b"
        for m in re.finditer(pat, text):
            hits.append((m.start(), ing))
    seen, out = set(), []
    for _, ing in sorted(hits):
        if ing not in seen:
            seen.add(ing); out.append(ing)
    return out


def _sub_order(words: list[str], drugs: list[str]) -> tuple[str, str]:
    """(new, old) for a substitution question. "X instead of Y", "X in place of Y", "X rather than Y",
    "X vs Y", "X better than Y" put the NEW drug first; "swap/trade/switch/change X for/to Y" and
    "from X to Y" put the OLD drug first."""
    a, b = drugs[0], drugs[1]
    t = " ".join(words)
    old_first = bool(re.search(r"\b(swap|swapped|swapping|trade|trading|switch|switching|switched|change|changing|"
                               r"changed|go|going|move|moving|from|replace|replacing)\b.*\b(for|to|with)\b", t))
    # "replace X with Y" is old-first; "X instead of Y" and "X in place of Y" are new-first
    if re.search(r"\b(instead of|in place of|rather than|vs|versus|better than|over)\b", t) and not re.search(
            r"\b(swap|trade|switch|change|changing|from)\b", t):
        old_first = False
    return (b, a) if old_first else (a, b)


def _context_drugs(old: str, new: str, flags: list[Flag]) -> list[str]:
    """Drugs of the user's own flags that share the drug being replaced ("with my clopidogrel")."""
    from .validator import _key_drugs
    ctx = []
    for f in flags:
        ds = _key_drugs(f.key)
        if old in ds:
            ctx += [d for d in sorted(ds) if d not in (old, new) and d not in ctx]
    return ctx


def _join(drugs: list[str]) -> str:
    names = [d.replace("_", " ") for d in drugs]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _rule_intent(words: list[str], drugs: list[str]) -> tuple[Optional[str], float]:
    """Deterministic cue rules -> (kind, confidence). None when no rule fires."""
    ws = set(words)
    n = len(drugs)
    if ws & _SUB_CUES and n >= 2:
        return "sub", 0.95
    if ws & _SUB_CUES and n == 1:
        return "sub1", 0.6
    if "cardiologist" in ws and n == 0:
        return "cardio", 0.9
    if "pharmacist" in ws and n == 0:
        return "pharm", 0.9
    if ws & {"follow-up", "followup", "visit", "appointment"} and ws & _LAB_WORDS and n == 0:
        return "followup", 0.9
    if ws & _LAB_WORDS and (n >= 1 or ws & {"statin", "medications", "medication", "medicine", "meds", "pills"}):
        return "lab", 0.9
    if ws & _GENE_WORDS and n >= 1:
        return "gene", 0.9
    if n >= 2:
        return "pair", 0.85
    if n == 1 and ws & _RX_CUES:
        return "rx", 0.8
    if n == 1 and ws & (_TAKE_CUES | {"headache", "pain", "medications", "medication", "meds", "medicine"}):
        return "otc", 0.8
    return None, 0.0


def _similar(words: list[str]) -> list[tuple[float, Intent]]:
    mine = _content_tokens(_slot(words))
    scored = []
    for it in intents():
        if not mine or not it.tokens:
            continue
        j = len(mine & it.tokens) / len(mine | it.tokens)
        scored.append((j, it))
    scored.sort(key=lambda s: -s[0])
    return scored


def _rewrite(kind: str, words: list[str], drugs: list[str], flags: list[Flag]) -> tuple[Optional[str], Optional[str]]:
    """Canonical wording for the cue family with the user's own drugs in the slots -> (text, intent id)."""
    ws = set(words)
    labs = [w for w in words if w in _LAB_WORDS]
    lab = " and ".join(dict.fromkeys(labs)) if labs else "labs"
    if kind == "sub":
        new, old = _sub_order(words, drugs)
        ctx = _context_drugs(old, new, flags)
        tail = f" with my {_join(ctx)}" if ctx else ""
        return f"Could {_join([new])} work instead of {_join([old])}{tail}?", "Q07" if ctx else "Q17"
    if kind == "cardio":
        return "What should I bring up with my cardiologist?", "Q18"
    if kind == "pharm":
        return "Which of my new prescriptions should I ask my pharmacist about first?", "Q19"
    if kind == "followup":
        return f"What should I ask at my follow-up about my {lab} and blood pressure medicine?", "Q20"
    if kind == "lab":
        if not drugs and "statin" in ws:   # "my statin" = the statin on the user's own med list (local flags)
            from .validator import _key_drugs
            drugs = sorted({d for f in flags for d in _key_drugs(f.key) if d.endswith("statin")})
        subj = f"my {_join(drugs)}" if drugs else ("my statin" if "statin" in ws else "my medications")
        qid = {"potassium": "Q11", "kidney": "Q12", "kidneys": "Q12", "egfr": "Q12", "renal": "Q12",
               "ck": "Q13", "cpk": "Q13", "kinase": "Q13", "liver": "Q14", "alt": "Q14"}.get(labs[0] if labs else "", "Q11")
        return f"Does my {lab} matter for {subj}?", qid
    if kind == "gene":
        if ws & {"dose", "doses", "mg"} and len(drugs) == 1:
            return f"Does my {_join(drugs)} dose make sense with my genes?", "Q02"
        return f"Would my genes matter for {_join(drugs)}?", "Q04"
    if kind == "pair":
        return f"Does {_join(drugs[:1])} interact with {_join(drugs[1:])}?", "Q09"
    if kind == "rx":
        return f"I was just prescribed {_join(drugs)}. Anything I should know?", "Q01"
    if kind == "otc":
        return f"Can I take {_join(drugs)} with my medications?", "Q15"
    return None, None


# optional layer d: local model ---------------------------------------------------------------------

def _llm_pick(question: str) -> Optional[str]:
    """GV_INTENT_LLM=1 only. Ask the local model (localhost Ollama, core.local_llm) for ONE canonical id
    from the closed list, or "none". Anything not in the list is treated as "none". Never adds text."""
    if os.environ.get("GV_INTENT_LLM", "").strip() != "1":
        return None
    try:
        from . import local_llm
        menu = "\n".join(f"{it.id}: {it.canonical}" for it in intents())
        raw = local_llm.generate(
            prompt=f"Question: {question}\n\nCanonical questions:\n{menu}\n\nAnswer with JSON {{\"id\": \"Qnn\" or \"none\"}}.",
            system="Pick the ONE canonical question that means the same as the user's question, or none.",
            format="json")
        pick = json.loads(raw).get("id")
    except Exception:
        return None
    return pick if pick in {it.id for it in intents()} else None


# entry point -----------------------------------------------------------------------------------------

def canonicalize(question: str, flags: Optional[list[Flag]] = None) -> Understanding:
    flags = flags or []
    original = question
    text, drug_fixes = _repair_drugs(question)
    drugs_map = _drug_spans(text)
    raw_words = set(_WORD_RE.findall(text.lower()))
    words, subs = _normalize_words(text)
    words, word_fixes = _repair_words(words, drugs_map)
    drugs = _find_drugs(words, drugs_map)
    u = Understanding(question=original, drugs=drugs, repairs=drug_fixes + word_fixes)
    if raw_words & _GUARD:   # someone else's question, or start/stop/dose-change advice (I7): never remapped
        return u

    kind, conf = _rule_intent(words, drugs)
    unknown = [w for w in words if w not in _vocab() and not w.isdigit() and len(w) >= 4
               and not _is_drug_word(w, drugs_map) and w not in {"statin"}]
    if unknown and kind not in (None, "cardio", "pharm", "followup"):
        # An unrepaired word next to drug names may itself be a (misspelled or unknown) drug: never
        # rewrite around it (I4). The original is routed unchanged; the UI may show the closest wording.
        u.clarify = [it.canonical for it in intents() if it.kind == kind][:3]
        u.confidence = 0.0
        return u
    if kind == "sub1":          # "what about X instead": the drug being replaced is not named -> ask
        u.clarify = [it.canonical for it in intents() if it.kind == "sub"]
        u.confidence = conf
        return u
    if kind is not None:
        rewritten, qid = _rewrite(kind, words, drugs, flags)
        if rewritten:
            u.question, u.rewritten, u.intent_id, u.confidence = rewritten, True, qid, conf
            if rewritten.lower() != original.lower():
                u.understood_as = rewritten
            return u

    scored = _similar(words)
    if scored:
        best, second = scored[0], (scored[1] if len(scored) > 1 else (0.0, None))
        if best[0] >= 0.6 and best[0] - second[0] >= 0.2 and not best[1].kind in {"sub", "pair", "gene", "lab", "rx", "otc"}:
            # only drug-free canonical questions can be matched by wording alone (I4: no drug is inferred)
            u.question, u.rewritten, u.intent_id, u.confidence = best[1].canonical, True, best[1].id, best[0]
            u.understood_as = best[1].canonical
            return u
        pick = _llm_pick(original)
        if pick:
            it = next(i for i in intents() if i.id == pick)
            if it.kind in {"cardio", "pharm", "followup"}:    # drug-free intents only: nothing inferred
                u.question, u.rewritten, u.intent_id, u.confidence = it.canonical, True, it.id, 0.7
                u.understood_as = it.canonical
                return u
        if best[0] >= 0.3:
            u.clarify = [it.canonical for s, it in scored[:3] if s >= 0.3]
            u.confidence = best[0]
    return u
