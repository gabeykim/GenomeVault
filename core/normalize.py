"""M3 normalize: free text (typed name or OCR'd label) -> generic ingredients (PLAN F2, M3).

`to_ingredients(text)` finds every known brand or generic name in the text, splits combination
products into their ingredients, and attaches a dose when the text gives one. Names come only from
`data/rules/drug_names.json`; there is no fuzzy matching, so an unknown or misspelled name gives `[]`
rather than a guess (same spirit as I4: no extrapolation).
"""
from __future__ import annotations

import functools
import json
import pathlib
import re

from .contracts import Drug

NAMES_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "rules" / "drug_names.json"

_WORD = re.compile(r"[a-z]+(?:-[a-z]+)*")
_NUMS = r"\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)*"
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
    parts = [float(p) * factor for p in re.split(r"\s*/\s*", m.group(1))]
    if len(parts) != n_ingredients:
        return [None] * n_ingredients                # strengths don't line up with ingredients
    return [round(p, 3) for p in parts]


def to_ingredients(text: str) -> list[Drug]:
    """Every recognized drug in `text` as `Drug(ingredient, dose_mg)`, in order of appearance,
    one entry per ingredient. Unknown text returns `[]`."""
    if not text or not text.strip():
        return []
    text = text.lower().replace("®", " ").replace("™", " ")
    lex, longest = _lexicon()
    toks = _tokens(text)

    matches: list[tuple[tuple[str, ...], int, int]] = []   # (ingredients, start, end)
    i = 0
    while i < len(toks):
        for n in range(min(longest, len(toks) - i), 0, -1):          # longest name first
            key = tuple(t for t, _, _ in toks[i:i + n])
            if key in lex:
                matches.append((lex[key], toks[i][1], toks[i + n - 1][2]))
                i += n
                break
        else:
            i += 1

    drugs: dict[str, Drug] = {}
    for j, (ingredients, _, end) in enumerate(matches):
        stop = matches[j + 1][1] if j + 1 < len(matches) else len(text)
        for ing, dose in zip(ingredients, _dose(text[end:stop], len(ingredients))):
            if ing not in drugs:
                drugs[ing] = Drug(ingredient=ing, dose_mg=dose)
            elif drugs[ing].dose_mg is None and dose is not None:
                drugs[ing] = Drug(ingredient=ing, dose_mg=dose)
    return list(drugs.values())
