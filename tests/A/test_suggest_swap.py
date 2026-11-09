"""D-041 interop: C's UI swaps the suggested name into the typed text and re-runs the exact path.

C-030 swaps `term` case-insensitively on word boundaries, where a hyphen counts as part of the
word (`(?<![\\w-])term(?![\\w-])`). A swap by `span` must always work; a swap by `term` must work
for every plain word. These tests pin what `suggest()` gives C so the two don't drift (to-A 1708).
"""
from __future__ import annotations

import re

import pytest

from core.normalize import suggest, to_ingredients


@pytest.fixture
def fuzzy(monkeypatch):
    monkeypatch.setenv("GV_FUZZY", "1")


def _c_swap(text: str, term: str, name: str) -> str:
    """C's `app._swap` as of C-030 (13374a9)."""
    return re.sub(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lambda _m: name, text, count=1,
                  flags=re.IGNORECASE)


def _span_swap(text: str, span: list[int], name: str) -> str:
    a, b = span
    return text[:a] + name + text[b:]


def _ings(text: str) -> list[str]:
    return [d.ingredient for d in to_ingredients(text)]


PLAIN = [
    ("Simvastatn 40mg", "simvastatin"),
    ("I take Atorvastatn every morning", "atorvastatin"),
    ("my Warfrin® dose", "warfarin"),
]

HYPHENATED = [
    ("lisinoprl-hydrochlorothiazide 10-12.5 mg", ["lisinopril", "hydrochlorothiazide"]),
]


@pytest.mark.parametrize("typed,meant", PLAIN)
def test_term_and_span_name_the_typed_word(fuzzy, typed, meant):
    [s] = suggest(typed)
    a, b = s["span"]
    assert typed[a:b].lower() == s["term"]          # span indexes the original text
    assert s["assumed"] == meant
    assert meant in _ings(_c_swap(typed, s["term"], s["assumed"]))
    assert meant in _ings(_span_swap(typed, s["span"], s["assumed"]))


@pytest.mark.parametrize("typed,meant", HYPHENATED)
def test_hyphenated_typo_swaps_by_span(fuzzy, typed, meant):
    """A typo inside a hyphenated combo is one part of the word. Swapping by span recovers both
    ingredients; C's term regex treats the hyphen as part of the word and leaves the text as is."""
    out = suggest(typed)
    fixed = typed
    for s in reversed(out):
        assert s["mode"] == "assumed", s
        fixed = _span_swap(fixed, s["span"], s["assumed"])
    assert _ings(fixed) == meant
    for s in out:
        assert _c_swap(typed, s["term"], s["assumed"]) == typed   # documents the gap told to C
