"""D-040 part 1: normalize.suggest proposes spellings for unmatched words, behind GV_FUZZY (F2, M3, I4).

Safety properties tested here: nothing changes with the flag off; to_ingredients never uses a
guess; look-alike names are always "ask"; every "assumed" answer is the drug that was meant.
"""
import json

import pytest

from core.normalize import LOOKALIKES_PATH, _lexicon, suggest, to_ingredients


@pytest.fixture
def fuzzy(monkeypatch):
    monkeypatch.setenv("GV_FUZZY", "1")


def _one(text):
    out = suggest(text)
    assert len(out) == 1, out
    return out[0]


def _ings(name):
    return [d.ingredient for d in to_ingredients(name)]


# A's typo set (shared with D for the D-040 part 5 typo eval). (typed, mode, meant name, meant ingredient)
ASSUMED = [
    ("simvastain", "simvastatin", "simvastatin"),
    ("omeprazol", "omeprazole", "omeprazole"),
    ("warfrin", "warfarin", "warfarin"),
    ("warafrin", "warfarin", "warfarin"),               # swapped letters count as one edit
    ("atorvastatn", "atorvastatin", "atorvastatin"),
    ("lisinoprl", "lisinopril", "lisinopril"),
    ("ibuprofin", "ibuprofen", "ibuprofen"),
    ("tylenl", "tylenol", "acetaminophen"),
    ("aspirn", "aspirin", "aspirin"),
    ("zolofft", "zoloft", "sertraline"),
    ("prilosc", "prilosec", "omeprazole"),
    ("citalopran", "citalopram", "citalopram"),
    ("rifampn", "rifampin", "rifampin"),
]
ASK = [   # look-alike names, or no single clear winner: the user must pick
    ("clopidogrl", "clopidogrel"),
    ("clonidne", "clonidine"),
    ("clozapin", "clozapine"),          # not covered: must not be steered to clonidine/clopidogrel
    ("celebrx", "celebrex"),
    ("tramdol", "tramadol"),
    ("plavx", "plavix"),
    ("fluoxetin", "fluoxetine"),
    ("hydroxyzin", "hydroxyzine"),      # not covered
    ("metformn", "metformin"),
    ("fenytoin", "phenytoin"),          # first letter changed: never assumed
    ("lasixx", "lasix"),
    ("imdurr", "imdur"),
]


def test_flag_off_returns_nothing(monkeypatch):
    monkeypatch.delenv("GV_FUZZY", raising=False)
    assert suggest("clopidogrl and simvastain") == []
    monkeypatch.setenv("GV_FUZZY", "0")
    assert suggest("clopidogrl and simvastain") == []


@pytest.mark.parametrize("typed,meant,ingredient", ASSUMED)
def test_assumed_is_the_meant_drug(fuzzy, typed, meant, ingredient):
    s = _one(f"can I take {typed} with food?")
    assert s["mode"] == "assumed" and s["choices"] == [meant] and s["not_covered"] == []
    assert _ings(meant) == [ingredient]


@pytest.mark.parametrize("typed,meant", ASK)
def test_ask_offers_the_meant_name(fuzzy, typed, meant):
    s = _one(typed)
    assert s["mode"] == "ask"
    assert meant in s["choices"] and 1 <= len(s["choices"]) <= 3


def test_typo_set_has_zero_silent_wrong_substitutions(fuzzy):
    """Across the whole set, no word is ever 'assumed' to be a different drug than the one meant."""
    meant = {t: m for t, m, _ in ASSUMED} | dict(ASK)
    assert len(meant) >= 20
    for typed, name in meant.items():
        for s in suggest(typed):
            if s["mode"] == "assumed":
                assert _ings(s["choices"][0]) == _ings(name), typed


def _one_edit_variants(word):
    out = {word[:i] + word[i + 1:] for i in range(len(word))}                         # deletions
    out |= {word[:i] + word[i + 1] + word[i] + word[i + 2:] for i in range(len(word) - 1)}  # swaps
    return out - {word}


def test_every_lookalike_near_miss_is_ask(fuzzy):
    groups = json.loads(LOOKALIKES_PATH.read_text())["groups"]
    for name in {n for g in groups for n in g}:
        for typed in _one_edit_variants(name):
            for s in suggest(typed):
                assert s["mode"] == "ask", (typed, s)


@pytest.mark.parametrize("text", ["clozapine", "prednisolone", "hydroxyzine", "klonopin"])
def test_exact_name_we_do_not_cover_gets_no_guess(fuzzy, text):
    assert suggest(text) == []
    assert to_ingredients(text) == []


@pytest.mark.parametrize("text", [
    "Can I take Plavix with omeprazole?",
    "Is it safe to take my blood pressure pills with grapefruit juice?",
    "I have a headache, can I take advil and tylenol together",
    "the patient is a player and a doctor at the clinic, prescribed cholesterol medication",
    "toprol xl 50 mg and zoloft",
    "Tylenol with codeine 300/30 mg",
])
def test_plain_questions_and_known_names_get_no_suggestion(fuzzy, text):
    assert suggest(text) == []


def test_to_ingredients_never_uses_a_guess(fuzzy):
    """I4: the flag only adds suggestions; the exact path still returns nothing for a typo."""
    for typed, *_ in ASSUMED + ASK:
        assert to_ingredients(typed) == []


def test_corrected_text_reenters_exact_path(fuzzy):
    text = "my doctor gave me simvastatn and plavx"
    out = suggest(text)
    assert [s["token"] for s in out] == ["simvastatn", "plavx"]
    for s in out:
        a, b = s["span"]
        assert text[a:b] == s["token"]
    fixed = text
    for s in reversed(out):
        a, b = s["span"]
        fixed = fixed[:a] + s["choices"][0] + fixed[b:]
    assert _ings(fixed) == ["simvastatin", "clopidogrel"]


def test_choices_are_recognized_or_marked_not_covered(fuzzy):
    for typed, *_ in ASSUMED + ASK:
        for s in suggest(typed):
            for c in s["choices"]:
                assert (c in s["not_covered"]) == (to_ingredients(c) == []), (typed, c)


def test_lookalike_table_shape():
    data = json.loads(LOOKALIKES_PATH.read_text())
    lex, _ = _lexicon()
    assert data["version"].startswith("lookalikes-v")
    for group in data["groups"]:
        assert len(group) >= 2 and all(n == n.lower() and " " not in n for n in group)
        assert any((n,) in lex for n in group), group      # each group protects a covered name
