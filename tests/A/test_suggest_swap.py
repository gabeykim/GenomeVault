"""D-041 interop: C's UI swaps the suggested name into the typed text and re-runs the exact path.

Since PR #16 and #17 are both on main, these tests run C's real `app._swap` / `/api/check` with
`GV_FUZZY` on, instead of a copy of C's regex (A-034 kept a copy; it could drift). They pin what
`suggest()` gives C (to-A 1708) and one property the banner relies on: every name the banner says
was assumed is a drug the check actually ran on (I4: the user sees what was looked up).
Local endpoint only: nothing here calls route() or the cloud (I2).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core.normalize import suggest, to_ingredients

client = TestClient(app_module.app)    # no `with`: the lifespan (cover traffic) never starts


@pytest.fixture
def fuzzy(monkeypatch):
    monkeypatch.setenv("GV_FUZZY", "1")


def _span_swap(text: str, span: list[int], name: str) -> str:
    a, b = span
    return text[:a] + name + text[b:]


def _ings(text: str) -> list[str]:
    return [d.ingredient for d in to_ingredients(text)]


def _check(text: str) -> dict:
    r = client.post("/api/check", json={"text": text})
    assert r.status_code == 200, r.text
    return r.json()


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
    assert meant in _ings(app_module._swap(typed, s["term"], s["assumed"]))
    assert meant in _ings(_span_swap(typed, s["span"], s["assumed"]))


@pytest.mark.parametrize("typed,meant", PLAIN)
def test_app_check_runs_on_the_assumed_name(fuzzy, typed, meant):
    out = _check(typed)
    assert [x["name"] for x in out["assumed"]] == [meant]
    assert meant in [d["ingredient"] for d in out["drugs"]]


@pytest.mark.parametrize("typed,meant", HYPHENATED)
def test_hyphenated_typo_swaps_by_span(fuzzy, typed, meant):
    """A typo inside a hyphenated combo is one part of the word. Swapping by span recovers both
    ingredients, which is what C's swap should match (to-C 1720)."""
    out = suggest(typed)
    fixed = typed
    for s in reversed(out):
        assert s["mode"] == "assumed", s
        fixed = _span_swap(fixed, s["span"], s["assumed"])
    assert _ings(fixed) == meant


@pytest.mark.xfail(reason="C's _swap skips a term inside a hyphenated word (to-C 1720); "
                          "passes once C swaps by span", strict=False)
@pytest.mark.parametrize("typed,meant", HYPHENATED)
def test_app_banner_names_only_checked_drugs_hyphenated(fuzzy, typed, meant):
    out = _check(typed)
    checked = {d["ingredient"] for d in out["drugs"]}
    for x in out.get("assumed", []):
        assert x["name"] in checked, (x, sorted(checked))


@pytest.mark.parametrize("typed,_meant", PLAIN)
def test_flag_off_is_unchanged(monkeypatch, typed, _meant):
    monkeypatch.delenv("GV_FUZZY", raising=False)
    out = _check(typed)
    assert "assumed" not in out and not out.get("held")
