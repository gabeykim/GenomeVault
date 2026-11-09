"""M3 normalize: free text (typed name or OCR'd label) -> generic ingredients (PLAN F2, M3).

`to_ingredients(text)` finds every known brand or generic name in the text, splits combination
products into their ingredients, and attaches a dose when the text gives one. Names come only from
`data/rules/drug_names.json`; there is no fuzzy matching, so an unknown or misspelled name gives `[]`
rather than a guess (same spirit as I4: no extrapolation).

`suggest(text)` (D-040 part 1, only when `GV_FUZZY=1`) proposes spellings for words that matched
no name, for the UI to show. It never changes what `to_ingredients` returns: a suggestion only
becomes a lookup after the user sees it and the corrected text goes back through the exact path.
"""
from __future__ import annotations

import functools
import json
import os
import pathlib
import re

from .contracts import Drug

NAMES_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "rules" / "drug_names.json"

_WORD = re.compile(r"[a-z]+(?:-[a-z]+)*")
_NUMS = r"\d+(?:\.\d+)?(?:\s*[/-]\s*\d+(?:\.\d+)?)*"   # "20/12.5" and "10-40": one strength per ingredient
_JOIN = re.compile(r"\s*[/-]\s*")                     # "ezetimibe-simvastatin", "lisinopril / hctz": one product
_UNIT = r"mg|mcg|ug|µg|g"
_DOSE_IMMEDIATE = re.compile(rf"^\s*({_NUMS})\s*({_UNIT})?(?![a-z0-9])")
_DOSE_WITH_UNIT = re.compile(rf"({_NUMS})\s*({_UNIT})(?![a-z0-9])")
_TO_MG = {"mg": 1.0, "g": 1000.0, "mcg": 0.001, "ug": 0.001, "µg": 0.001}


@functools.lru_cache(maxsize=1)
def _lexicon() -> tuple[dict[tuple[str, ...], tuple[str, ...]], int]:
    """name tokens -> ingredients; plus the longest name length in tokens."""
    raw = json.loads(NAMES_PATH.read_text())["names"]
    lex: dict[tuple[str, ...], tuple[str, ...]] = {}
    for name, ingredients in raw.items():
        lex[_name_key(name)] = tuple(i.lower() for i in ingredients)
        for ing in ingredients:                      # every ingredient is known under its own name
            lex.setdefault(_name_key(ing), (ing.lower(),))
    return lex, max(len(k) for k in lex)


def _name_key(name: str) -> tuple[str, ...]:
    """A table name as the word tokens the text would produce: "St. John's wort" and the
    ingredient id "st_johns_wort" both become words, the same way `_tokens` splits input."""
    return tuple(_WORD.findall(name.lower().replace("_", " ")))


def _tokens(text: str) -> list[tuple[str, int, int]]:
    """Lowercase word tokens with spans. A hyphenated word that is not itself a known name is
    split into its parts, so "lisinopril-hydrochlorothiazide" yields both ingredients."""
    lex, _ = _lexicon()
    out = []
    for m in _WORD.finditer(text):
        word = m.group()
        if "-" not in word or (word,) in lex:
            out.append((word, m.start(), m.end()))
            continue
        pos = m.start()
        for part in word.split("-"):
            out.append((part, pos, pos + len(part)))
            pos += len(part) + 1
    return out


def _dose(window: str, n_ingredients: int) -> list[float | None]:
    """Dose(s) in mg from the text between this name and the next one."""
    m = _DOSE_IMMEDIATE.match(window)
    if m and not m.group(2) and re.match(r"\s*[a-z]", window[m.end():]):
        m = None                                     # "aspirin 2 tablets": a bare count, not a dose
    if not m:
        m = _DOSE_WITH_UNIT.search(window)
    if not m:
        return [None] * n_ingredients
    factor = _TO_MG[m.group(2) or "mg"]
    parts = [float(p) * factor for p in _JOIN.split(m.group(1))]
    if len(parts) != n_ingredients:
        return [None] * n_ingredients                # strengths don't line up (or a range): unknown, never a guess
    return [round(p, 3) for p in parts]


def _clean(text: str) -> str:
    return text.lower().replace("®", " ").replace("™", " ")


def _matches(text: str) -> list[tuple[tuple[str, ...], int, int]]:
    """Exact lexicon names in cleaned `text`, longest name first: (ingredients, start, end)."""
    lex, longest = _lexicon()
    toks = _tokens(text)
    matches: list[tuple[tuple[str, ...], int, int]] = []
    i = 0
    while i < len(toks):
        for n in range(min(longest, len(toks) - i), 0, -1):
            key = tuple(t for t, _, _ in toks[i:i + n])
            if key in lex:
                matches.append((lex[key], toks[i][1], toks[i + n - 1][2]))
                i += n
                break
        else:
            i += 1
    return matches


def to_ingredients(text: str) -> list[Drug]:
    """Every recognized drug in `text` as `Drug(ingredient, dose_mg)`, in order of appearance,
    one entry per ingredient. Unknown text returns `[]`."""
    if not text or not text.strip():
        return []
    text = _clean(text)
    matches = _matches(text)

    # Names joined only by "-" or "/" are one combination product, and the strengths after the last
    # name belong to all of them in order: "ezetimibe-simvastatin 10-40 mg" is simvastatin 40 mg.
    groups: list[tuple[tuple[str, ...], int, int]] = []
    for ingredients, start, end in matches:
        if groups and _JOIN.fullmatch(text[groups[-1][2]:start]):
            groups[-1] = (groups[-1][0] + ingredients, groups[-1][1], end)
        else:
            groups.append((ingredients, start, end))

    drugs: dict[str, Drug] = {}
    for j, (ingredients, _, end) in enumerate(groups):
        stop = groups[j + 1][1] if j + 1 < len(groups) else len(text)
        for ing, dose in zip(ingredients, _dose(text[end:stop], len(ingredients))):
            if ing not in drugs:
                drugs[ing] = Drug(ingredient=ing, dose_mg=dose)
            elif drugs[ing].dose_mg is None and dose is not None:
                drugs[ing] = Drug(ingredient=ing, dose_mg=dose)
    return list(drugs.values())


# --- D-040 part 1: typo suggestions (GV_FUZZY=1) -------------------------------------------

LOOKALIKES_PATH = NAMES_PATH.parent / "lookalikes.json"
ASSUME_MAX = 2           # "assumed" needs the best candidate within 2 edits ...
ASSUME_GAP = 2           # ... and every candidate meaning another drug at least 2 edits further
MAX_CHOICES = 3
MIN_TOKEN = 4            # shorter words ("mg", "xl", "can") are never treated as typos

# Common question words long enough to be suggest-able. Never a typo for a drug name.
_STOPWORDS = frozenset("""
    about after again alcohol allergic allergy also anything before blood both coffee combine
    combined could daily days does doctor dose doses drink drinks each effects every feel food
    gave given grapefruit have headache heart help high interact interaction interactions juice
    just like medicine meds mixing morning night nurse okay once only other pain pharmacist pill
    pills prescribed prescription pressure safe should side some start started still stop stopped
    tablet tablets take taken takes taking than that their them then there these they this
    together twice using water week weeks what when where which while will with would years your
""".split())


def fuzzy_enabled() -> bool:
    return os.environ.get("GV_FUZZY", "").strip().lower() in {"1", "true", "yes", "on"}


def _limit(token: str) -> int:
    """Edits a word may be from a name and still count as a candidate."""
    n = len(token)
    return 1 if n <= 6 else 2 if n <= 9 else 3     # short words: "player" is not "bayer"


def _distance(a: str, b: str, cap: int) -> int:
    """Edit distance with adjacent swaps counting as one edit (optimal string alignment).
    Returns cap + 1 as soon as the answer must exceed `cap`."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > cap:
            return cap + 1
        prev2, prev = prev, cur
    return prev[-1]


@functools.lru_cache(maxsize=1)
def _suggest_tables():
    """(candidate name -> ingredients, or None for a look-alike we have no tables for;
    name -> the other names in its look-alike groups; words inside multi-word names)."""
    lex, _ = _lexicon()
    names: dict[str, tuple[str, ...] | None] = {k[0]: v for k, v in lex.items() if len(k) == 1}
    parts = frozenset(w for k in lex if len(k) > 1 for w in k)
    groups: dict[str, list[str]] = {}
    for group in json.loads(LOOKALIKES_PATH.read_text())["groups"]:
        group = [g.lower() for g in group]
        for g in group:
            mates = groups.setdefault(g, [])
            mates += [x for x in group if x != g and x not in mates]
            names.setdefault(g, None)
    return names, groups, parts


def suggest(text: str) -> list[dict]:
    """Spelling suggestions for the words in `text` that matched no drug name (D-040 part 1).

    Returns [] unless GV_FUZZY=1. Otherwise one dict per suggest-able word, in text order:
        {"token": str, "term": str,     # the same word (C reads "term")
         "span": [start, end], "mode": "assumed" | "ask",
         "assumed": name | None,        # set only when mode == "assumed"
         "choices": [name, ...],        # 1 to 3, best first; "assumed" has exactly 1
         "not_covered": [name, ...]}    # choices that are real drugs with no GenomeVault tables
    "assumed": one name within 2 edits and nothing meaning another drug within 2 more; the UI
    shows "I'm assuming you mean X" with an undo. "ask": the UI shows "Did you mean ...?" and
    waits. A word near any name in data/rules/lookalikes.json is always "ask". Choices are spelled
    so that to_ingredients() recognizes them (not_covered ones give [], i.e. no_data)."""
    if not fuzzy_enabled() or not text or not text.strip():
        return []
    text = _clean(text)
    names, groups, parts = _suggest_tables()
    covered = [(s, e) for _, s, e in _matches(text)]
    out: list[dict] = []
    for token, start, end in _tokens(text):
        if (len(token) < MIN_TOKEN or token in _STOPWORDS or token in parts
                or any(s <= start and end <= e for s, e in covered)):
            continue
        if token in names:            # spells a look-alike we have no tables for ("clozapine"): no guess
            continue
        cap = _limit(token)
        ranked = sorted((d, name) for name in names if (d := _distance(token, name, cap)) <= cap)
        if not ranked:
            continue
        best_d, best = ranked[0]
        near_lookalike = [name for _, name in ranked if name in groups]
        others = [d for d, name in ranked[1:] if names[name] is None or names[name] != names[best]]
        if (not near_lookalike and names[best] is not None and best_d <= ASSUME_MAX
                and best[0] == token[0]                       # typos rarely change the first letter
                and all(d >= best_d + ASSUME_GAP for d in others)):
            mode, choices = "assumed", [best]
        else:
            mode, choices, seen = "ask", [], set()
            for _, name in ranked:
                if names[name] is not None:
                    if names[name] in seen:
                        continue      # "rifampn": rifampin, not rifampicin as well
                    seen.add(names[name])
                choices.append(name)
            for name in near_lookalike:
                choices += [g for g in groups[name] if g not in choices]
            choices = choices[:MAX_CHOICES]
        out.append({"token": token, "term": token, "span": [start, end], "mode": mode,
                    "assumed": choices[0] if mode == "assumed" else None, "choices": choices,
                    "not_covered": [c for c in choices if names[c] is None]})
    return out
