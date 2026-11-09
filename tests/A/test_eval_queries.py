"""G2 support (D-030, integrator 1522): D's 20 eval questions resolve through A's code with no silent miss.

1. Every drug in `eval/queries.json` is an exact key in `normalize` (by its own name and, where the
   question names it, inside the question text). A class word ("my statin") gives no Drug (I4).
2. Every key a question lists is either a curated key that `rules` actually fires (or a D-021 expected
   note), or a deliberate `no_data` case (I4): never curated-but-silent.
3. `rules.check_all` output goes into `router.route` as plain contract `Flag`s and comes back as an
   `Answer` (the A→B handoff, CONTRACTS `rules.check` / `router.route`). Runs against B's real router
   once it is on main, against `core.interfaces.route` until then.

The questions are a frozen copy of D's q-v7 (eval/ is not on main yet). When `eval/queries.json` is
present, the same checks run on it too, so a new question or drug in D's file fails here first.
"""
import importlib
import json
import pathlib

import pytest

from core import graph, normalize, rules
from core.contracts import Answer, Drug, Flag

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIVE = ROOT / "eval" / "queries.json"

# id, text, drugs, keys, expected_flags, local_notes, expected_engines (D's q-v7, trimmed to what A checks).
Q_V7 = [
    ("Q01", "I was just prescribed clopidogrel 75 mg. Anything I should know?", ["clopidogrel"],
     ["CYP2C19:poor_metabolizer|clopidogrel"], ["X1"], [], []),
    ("Q02", "Does my simvastatin 40 mg dose make sense with my genes?", ["simvastatin"],
     ["SLCO1B1:decreased_function|simvastatin|dose>20mg"], ["X3"], [], []),
    ("Q03", "My doctor mentioned codeine for pain after a procedure. Would my genes affect how it works?",
     ["codeine"], ["CYP2D6:not_assessed|codeine"], [], [], []),
    ("Q04", "Would my genes matter if I ever needed warfarin?", ["warfarin"],
     ["CYP2C9:normal_metabolizer|warfarin", "VKORC1:normal_sensitivity|warfarin"], [], [], []),
    ("Q05", "If I'm prescribed citalopram for anxiety, could my genes affect it?", ["citalopram"],
     ["CYP2C19:poor_metabolizer|citalopram"], [], [], []),
    ("Q06", "Is it a problem that I take omeprazole with clopidogrel?", ["omeprazole", "clopidogrel"],
     ["clopidogrel|omeprazole"], ["X2"], [], []),
    ("Q07", "Could pantoprazole work instead of omeprazole with my clopidogrel?", ["pantoprazole", "clopidogrel"],
     ["clopidogrel|pantoprazole"], [], [], []),
    ("Q08", "Is there anything to know about taking aspirin and clopidogrel together?", ["aspirin", "clopidogrel"],
     ["aspirin|clopidogrel"], [], ["EX-001"], []),
    ("Q09", "Does simvastatin interact with lisinopril?", ["simvastatin", "lisinopril"],
     ["lisinopril|simvastatin"], [], [], []),
    ("Q10", "My cardiologist might add amlodipine. Does it interact with my simvastatin?", ["amlodipine", "simvastatin"],
     ["amlodipine|simvastatin"], [], [], []),
    ("Q11", "Is my lisinopril a concern given my latest potassium result?", ["lisinopril"],
     ["lisinopril|potassium>5.0"], ["X4"], [], []),
    ("Q12", "My kidney function dropped since last year. Does that matter for my lisinopril?", ["lisinopril"],
     ["lisinopril|potassium>5.0", "lisinopril|egfr<60"], ["X4"], [], []),
    ("Q13", "Does my CK level matter for my simvastatin?", ["simvastatin"], ["simvastatin|ck>1000"], ["X3"], [], []),
    ("Q14", "Are my liver tests a problem for my statin?", ["simvastatin"], ["simvastatin|alt>120"], ["X3"], [], []),
    ("Q15", "Can I take ibuprofen for a headache?", ["ibuprofen"],
     ["aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60"], ["X5"], [], []),
    ("Q16", "Can I take St. John's wort with my medications?", ["st_johns_wort"],
     ["clopidogrel|st_johns_wort", "simvastatin|st_johns_wort"], [], [], []),
    ("Q17", "What about naproxen instead of ibuprofen?", ["naproxen"],
     ["aspirin|naproxen", "clopidogrel|naproxen", "lisinopril|naproxen"], [], [], ["class_rule"]),
    ("Q18", "What should I bring up with my cardiologist?", [],
     ["CYP2C19:poor_metabolizer|clopidogrel", "clopidogrel|omeprazole",
      "SLCO1B1:decreased_function|simvastatin|dose>20mg", "lisinopril|potassium>5.0"], ["X1", "X2", "X3", "X4"], [], []),
    ("Q19", "Which of my new prescriptions should I ask my pharmacist about first?", [],
     ["CYP2C19:poor_metabolizer|clopidogrel", "clopidogrel|omeprazole"], ["X1", "X2"], [], []),
    ("Q20", "What should I ask at my follow-up about my kidney function and blood pressure medicine?", [],
     ["lisinopril|potassium>5.0", "lisinopril|egfr<60"], ["X4"], [], []),
]

# Questions that name a drug only by class. Mapping "statin" to simvastatin would be a guess (I4): the
# eval gives the drug directly, and the router reads the med list for the subject.
CLASS_WORD_ONLY = {"Q14"}


def _frozen() -> list[dict]:
    names = ("id", "text", "drugs", "keys", "expected_flags", "local_notes", "expected_engines")
    return [dict(zip(names, q)) for q in Q_V7]


def _live() -> list[dict]:
    if not LIVE.exists():
        return []
    return json.loads(LIVE.read_text())["queries"]


@pytest.fixture(scope="module")
def alex():
    return graph.load_profile()


def _med(profile, ingredient: str) -> Drug:
    """The drug as Alex takes it (dose matters for X3), or undosed if it is not on the med list."""
    return next((m for m in profile.meds if m.ingredient == ingredient), Drug(ingredient=ingredient))


def _fired(q: dict, profile) -> tuple[list[Flag], set[str]]:
    if not q["drugs"]:  # open-ended: the whole med list is the context
        return rules.check_all(profile), {n["key"] for n in rules.expected_notes_all(profile)}
    flags, notes = [], set()
    for d in q["drugs"]:
        flags += rules.check(_med(profile, d), profile)
        notes |= {n["key"] for n in rules.expected_notes(_med(profile, d), profile)}
    return flags, notes


def _is_pair(key: str) -> bool:
    parts = key.split("|")
    return len(parts) == 2 and ":" not in key and not any(op in key for op in "<>")


def _check_query(q: dict, profile) -> None:
    qid = q["id"]
    # 1. normalize: each drug is an exact key by its own name ...
    for d in q["drugs"]:
        got = [x.ingredient for x in normalize.to_ingredients(d.replace("_", " "))]
        assert got == [d], f"{qid}: {d!r} normalizes to {got}"
    # ... and inside the question, unless the question only uses a class word or names no drug.
    in_text = {x.ingredient for x in normalize.to_ingredients(q["text"])}
    if qid in CLASS_WORD_ONLY or not q["drugs"]:
        assert in_text == set(), f"{qid}: guessed {in_text} from a question that names no drug"
    else:
        assert set(q["drugs"]) <= in_text, f"{qid}: {q['text']!r} -> {in_text}"

    # 2. rules: curated keys fire; everything else is a deliberate no_data case.
    flags, note_keys = _fired(q, profile)
    fired_keys = {f.key for f in flags}
    no_data_pairs = {k for d in q["drugs"] for k in rules.no_data_keys(_med(profile, d), profile)}
    for k in q["keys"]:
        state = rules.key_state(k)
        if state == "known":
            assert k in fired_keys | note_keys, f"{qid}: {k} is curated but nothing fires for Alex"
        else:
            assert state == "no_data", f"{qid}: {k} -> {state}"
            assert k not in fired_keys, f"{qid}: {k} fired but is no_data"
            if _is_pair(k) and q["drugs"]:
                assert k in no_data_pairs, f"{qid}: {k} is no_data but not marked by no_data_keys"
    ids = {f.id for f in flags}
    assert set(q["expected_flags"]) <= ids, f"{qid}: expected {q['expected_flags']}, fired {sorted(ids)}"
    for f in flags:
        if f.key in q["keys"]:
            assert f.id in q["expected_flags"] or f.engine in q.get("expected_engines", []), (qid, f.id, f.key)
    notes = {n["id"] for d in q["drugs"] for n in rules.expected_notes(_med(profile, d), profile)}
    assert set(q.get("local_notes", [])) <= notes, f"{qid}: notes {sorted(notes)}"


@pytest.mark.parametrize("q", _frozen(), ids=lambda q: q["id"])
def test_q_v7_resolves_through_normalize_and_rules(q, alex):
    _check_query(q, alex)


@pytest.mark.skipif(not LIVE.exists(), reason="eval/queries.json is on D's branch until G2")
@pytest.mark.parametrize("q", _live() or [None], ids=lambda q: q["id"] if q else "none")
def test_live_queries_resolve_through_normalize_and_rules(q, alex):
    _check_query(q, alex)


def test_every_eval_drug_is_in_the_lexicon():
    drugs = {d for q in _frozen() + _live() for d in q["drugs"]}
    assert len(drugs) >= 13  # q-v7 names 13 distinct drugs
    for d in sorted(drugs):
        assert [x.ingredient for x in normalize.to_ingredients(d.replace("_", " "))] == [d], d


# --- 3. rules.check_all -> router.route (the A→B handoff) ----------------------------------------

def _router():
    try:
        return importlib.import_module("core.router")
    except ImportError:
        return None


@pytest.fixture
def route_offline(tmp_path, monkeypatch):
    """B's real router, offline and cold (nothing can be sent), or the interfaces stub before G2."""
    r = _router()
    if r is None:
        from core import interfaces
        yield interfaces.route, False
        return
    from core import kb, ledger
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("GV_OFFLINE", "1")
    if hasattr(r.cloud, "_forced"):
        monkeypatch.setattr(r.cloud, "_forced", None)
    ledger.reset()
    kb.reset()
    yield r.route, True
    ledger.reset()
    kb.reset()


def test_check_all_flags_are_plain_contract_flags(alex):
    flags = rules.check_all(alex)
    assert [f.id for f in flags] == ["X1", "X2", "X3", "X4"]
    for f in flags:
        assert type(f) is Flag
        assert Flag.model_validate_json(f.model_dump_json()) == f
    # X1/X2 ask general knowledge; X3/X4 are answered by the rule itself (P5, CONTRACTS needs_cloud).
    assert {f.id for f in flags if f.needs_cloud} == {"X1", "X2"}


@pytest.mark.parametrize("q", _frozen(), ids=lambda q: q["id"])
def test_check_all_feeds_route(q, alex, route_offline):
    route, real = route_offline
    flags = rules.check_all(alex)
    before = [f.model_dump() for f in flags]
    a = route(q["text"], flags)
    assert isinstance(a, Answer)
    assert Answer.model_validate_json(a.model_dump_json()) == a
    assert [f.model_dump() for f in flags] == before, "route must not change A's flags"
    if real:
        assert a.sent_to_cloud is False  # offline: 0 bytes (F8)
        assert a.state in ("known", "no_data")


@pytest.mark.parametrize("qid", ["Q02", "Q11", "Q15"])
def test_local_flags_answer_offline(qid, alex, route_offline):
    """X3, X4 and X5 are answered by A's rules alone (needs_cloud False), so offline and on a cold KB
    the real router still says `known` with 0 bytes (F8, S6). Caller flags = the med list plus the
    asked drug, as the app passes them (an OTC like ibuprofen is not on the med list)."""
    route, real = route_offline
    if not real:
        pytest.skip("core.router is on B's branch until G2")
    q = next(q for q in _frozen() if q["id"] == qid)
    asked = [f for d in q["drugs"] for f in rules.check(_med(alex, d), alex)]
    flags = list({f.key: f for f in rules.check_all(alex) + asked}.values())
    assert all(not f.needs_cloud for f in asked)
    a = route(q["text"], flags)
    assert (a.state, a.sent_to_cloud) == ("known", False)


def test_needs_cloud_flags_generalize_into_the_partition(alex):
    """Every flag A marks needs_cloud has a key B can generalize and bucket (I5): no silent drop."""
    r = _router()
    if r is None:
        pytest.skip("core.router is on B's branch until G2")
    from core.decoys import bucket_for
    from core.generalize import generalize
    for f in rules.check_all(alex):
        if not f.needs_cloud:
            continue
        topics = generalize(f)
        assert topics, f.key
        assert all(bucket_for(t.key) is not None for t in topics), [t.key for t in topics]
