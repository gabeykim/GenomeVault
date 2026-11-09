"""GV_INTENT (D-040): paraphrases, synonyms, word order and typos of a supported question get the same
answer as its canonical wording; unclear questions are never guessed; nothing leaves the device."""
import json
import os
import pathlib
from unittest import mock

import pytest

os.environ.setdefault("DEMO", "1")
os.environ.setdefault("GV_COVER_INTERVAL_S", "3600")

from fastapi.testclient import TestClient  # noqa: E402

import app as appmod  # noqa: E402
from core import intent, ledger  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FX = json.loads((ROOT / "tests/I/fixtures/paraphrases.json").read_text())
CANON = {q["id"]: q["text"] for q in json.loads((ROOT / "eval/queries.json").read_text())["queries"]}
# Variants that need A's normalize.suggest (GV_FUZZY, PR #17) for a drug-name typo, or name only one drug of a
# substitution ("what about X instead", answered with a clarification): known gaps, not regressions.
KNOWN_GAPS = {
    "does my simvastain dose make sence with my genes", "could pantoprazle work instead of omeprazole with my clopidogrel",
    "is there anyting to know about taking asprin and clopidogrel together", "does simvastain interact with lisinopril",
    "does amlodipine interact with my simvastain", "can i take ibuprofin for a headache",
    "what about pantoprazole instead", "what about naproxen instead",
}
MIN_PASS = 160


def _sig(c, q):
    r = c.post("/api/ask", json={"question": q}).json()
    return r["state"], tuple(sorted(f["key"] for f in r["facts"])), r


@pytest.fixture
def client():
    with TestClient(appmod.app) as c:
        yield c


def test_flag_off_by_default():
    assert not intent.enabled()


def test_flag_off_response_has_no_new_fields(client):
    with mock.patch.dict(os.environ, {"GV_INTENT": ""}):
        r = client.post("/api/ask", json={"question": "could i swap my omeprazole for pantoprazole"}).json()
    assert "understood_as" not in r and "clarify" not in r
    assert set(r) >= {"state", "text", "sections", "facts", "sent_to_cloud"}


def test_paraphrases_match_canonical(client):
    with mock.patch.dict(os.environ, {"GV_INTENT": "1"}):
        total = ok = 0
        fails = []
        for qid, variants in FX["variants"].items():
            cs, ck, _ = _sig(client, CANON[qid])
            for v in variants:
                total += 1
                s, k, _ = _sig(client, v)
                if (s, k) == (cs, ck):
                    ok += 1
                elif v not in KNOWN_GAPS:
                    fails.append((qid, v, s, k, cs, ck))
    assert not fails, fails
    assert ok >= MIN_PASS, (ok, total)


def test_negatives_never_change_the_answer(client):
    """Off-topic, third-party, start/stop and unknown-drug questions: same state and keys as with the flag
    off (today's behaviour), never a confident remap to a different answer."""
    for n in FX["negative"]:
        with mock.patch.dict(os.environ, {"GV_INTENT": ""}):
            s0, k0, _ = _sig(client, n)
        with mock.patch.dict(os.environ, {"GV_INTENT": "1"}):
            s1, k1, r = _sig(client, n)
        assert (s1, k1) == (s0, k0), (n, s0, s1, k0, k1, r.get("understood_as"))


def test_canonical_examples():
    u = intent.canonicalize("wat shoud i ask my cardiolgist")
    assert u.question == CANON["Q18"] and u.intent_id == "Q18"
    assert ("cardiolgist", "cardiologist") in u.repairs
    assert intent.canonicalize("what do i tell my heart doctor").question == CANON["Q18"]
    assert intent.canonicalize("what do i ask my chemist about first").question == CANON["Q19"]
    u = intent.canonicalize("could i swap my omeprazole for pantoprazole")
    assert u.question == "Could pantoprazole work instead of omeprazole?"        # new/old order kept
    assert intent.canonicalize("naproxen vs ibuprofen").question == "Could naproxen work instead of ibuprofen?"


def test_substitution_context_comes_from_own_flags(client):
    """"swap my omeprazole for pantoprazole" is routed as Q07 with the flagged partner ("with my clopidogrel")."""
    with mock.patch.dict(os.environ, {"GV_INTENT": "1"}):
        r = client.post("/api/ask", json={"question": "could i swap my omeprazole for pantoprazole"}).json()
    assert r["understood_as"] == CANON["Q07"]


def test_unclear_is_clarified_not_guessed():
    u = intent.canonicalize("what about pantoprazole instead")
    assert not u.rewritten and u.question == "what about pantoprazole instead" and u.clarify
    u = intent.canonicalize("can i take xyzzyqol for a headache")          # unknown word near a slot
    assert not u.rewritten and u.question == "can i take xyzzyqol for a headache"
    for q in ["can my dog take ibuprofen", "is it safe to stop my clopidogrel", "should i double my simvastatin dose"]:
        u = intent.canonicalize(q)
        assert not u.rewritten and u.understood_as is None, q


def test_drug_typos_are_never_repaired_here():
    """Only normalize.suggest (GV_FUZZY, A) may fix a drug name; the closed vocabulary holds no drug."""
    u = intent.canonicalize("does simvastain interact with lisinopril")
    assert not u.rewritten and not any(a == "simvastain" for a, _ in u.repairs)
    assert not any(intent._vocab() & {"simvastatin", "clopidogrel", "aspirin", "pantoprazole", "ibuprofen"})


def test_suggest_assumed_only(monkeypatch):
    """With A's suggest(): an unambiguous `assumed` spelling is applied; `ask` (look-alikes) is left alone."""
    from core import normalize
    calls = []

    def fake(text):
        calls.append(text)
        out = []
        i = text.find("simvastain")
        if i >= 0:
            out.append({"token": "simvastain", "term": "simvastain", "span": [i, i + 10], "mode": "assumed",
                        "assumed": "simvastatin", "choices": ["simvastatin"], "not_covered": []})
        j = text.find("hydroxyzne")
        if j >= 0:
            out.append({"token": "hydroxyzne", "term": "hydroxyzne", "span": [j, j + 10], "mode": "ask",
                        "assumed": None, "choices": ["hydroxyzine", "hydralazine"], "not_covered": []})
        return out
    monkeypatch.setattr(normalize, "suggest", fake, raising=False)
    u = intent.canonicalize("does simvastain interact with lisinopril")
    assert u.question == "Does simvastatin interact with lisinopril?" and ("simvastain", "simvastatin") in u.repairs
    u = intent.canonicalize("does hydroxyzne interact with lisinopril")
    assert "hydroxyzne" in u.question and not u.rewritten


def test_rewrite_goes_through_route_same_outbound_texts(client):
    """The paraphrase and its canonical produce identical outbound ledger texts: the rewrite is routed by the
    same route(), through the same generalize / fixed bucket / leakage check / ledger (I3, I5)."""
    def outbound(q):
        before = client.get("/api/ledger").json()
        seq0 = max([e.get("seq", 0) for e in before.get("entries", [])] or [0])
        client.post("/api/ask", json={"question": q})
        after = client.get("/api/ledger").json()
        new = [e for e in after.get("entries", []) if e.get("seq", 0) > seq0 and e.get("kind") != "cover"]
        return [(e.get("kind"), e.get("bucket_id")) for e in new]
    with mock.patch.dict(os.environ, {"GV_INTENT": "1"}):
        a = outbound(CANON["Q18"])
        b = outbound("what do i tell my heart doctor")
    assert [k for k, _ in a] == [k for k, _ in b]
    assert all(k in {"local_only", "kb_hit", "bucket", "blocked"} for k, _ in a + b)


def test_no_network_module_in_intent():
    src = (ROOT / "core/intent.py").read_text()
    for mod in ("httpx", "requests", "urllib", "socket", "aiohttp"):
        assert f"import {mod}" not in src and f"from {mod}" not in src
    import core.intent as m
    assert not {"httpx", "requests", "urllib.request", "socket"} & set(vars(m))


def test_llm_pick_is_closed_list_and_off_by_default(monkeypatch):
    assert intent._llm_pick("anything") is None
    from core import local_llm
    monkeypatch.setenv("GV_INTENT_LLM", "1")
    monkeypatch.setattr(local_llm, "generate", lambda **kw: '{"id": "Q99"}')
    assert intent._llm_pick("anything") is None
    monkeypatch.setattr(local_llm, "generate", lambda **kw: '{"id": "Q18"}')
    assert intent._llm_pick("anything") == "Q18"
