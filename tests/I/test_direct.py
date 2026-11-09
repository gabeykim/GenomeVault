"""GV_DIRECT: an answer-first lead line composed on device from flags, facts and states only (I4), never
saying the s-word or giving start/stop advice (I7); flag off -> byte-identical responses; ledger unchanged (I3)."""
import json
import os
import pathlib
from unittest import mock

import pytest

os.environ.setdefault("DEMO", "1")
os.environ.setdefault("GV_COVER_INTERVAL_S", "3600")

from fastapi.testclient import TestClient  # noqa: E402

import app as appmod  # noqa: E402
from core import direct, merge  # noqa: E402
from core.router import LOCAL_TEXT  # noqa: E402
from core.validator import wording_problems  # noqa: E402

EXAMPLES = ["What should I bring up with my cardiologist?", "what should i ask my heart doctor about",
            "Which of my new prescriptions should I ask my pharmacist about first?", "does ibuprofen help a headache",
            "Can I take ibuprofen for a headache?", "Could pantoprazole work instead of omeprazole with my clopidogrel?",
            "Does simvastatin interact with lisinopril?", "Can I take St. John's wort with my medications?",
            "is it a problem that i take omeprazole with clopidogrel", "does amlodipine interact with my simvastatin"]


@pytest.fixture
def client():
    with TestClient(appmod.app) as c:
        yield c


def _ask(c, q):
    return c.post("/api/ask", json={"question": q}).json()


def _lead(r):
    leads = [s for s in r["sections"] if s["kind"] == "lead"]
    return leads[0] if leads else None


def test_off_by_default_and_identical(client):
    with mock.patch.dict(os.environ, {"GV_DIRECT": ""}):
        r = _ask(client, "Can I take ibuprofen for a headache?")
    assert not direct.enabled()
    assert not any(s.get("direct") for s in r["sections"])


@pytest.mark.parametrize("gv_intent", ["", "1"])
def test_examples_lead_first(client, gv_intent):
    with mock.patch.dict(os.environ, {"GV_DIRECT": "1", "GV_INTENT": gv_intent}):
        r = _ask(client, "What should I bring up with my cardiologist?")
        lead = _lead(r)
        assert lead["direct"] and r["sections"][0] is lead or r["sections"][0] == lead
        assert lead["paragraphs"][0].startswith("Four things to raise with your cardiologist:")
        assert lead["paragraphs"][1].startswith("1. clopidogrel") and "(X1, high)" in lead["paragraphs"][1]
        assert r["text"].startswith("Four things to raise with your cardiologist:")

        r = _ask(client, "what should i ask my heart doctor about")
        assert _lead(r)["paragraphs"][0].startswith("Four things to raise with your")

        r = _ask(client, "Which of my new prescriptions should I ask my pharmacist about first?")
        assert _lead(r)["paragraphs"] == ["Start with clopidogrel: it appears in 2 of your high-priority flags (X1, X2)."]

        r = _ask(client, "does ibuprofen help a headache")
        line = _lead(r)["paragraphs"][0]
        assert line.startswith("GenomeVault does not answer whether a medicine works for a symptom")
        assert "ibuprofen is flagged against four things in your records: aspirin, clopidogrel" in line
        assert "eGFR 62 → 48" in line and "lisinopril" in line
        assert LOCAL_TEXT not in r["text"] and not any(LOCAL_TEXT in p for s in r["sections"] for p in s["paragraphs"])

        r = _ask(client, "Can I take ibuprofen for a headache?")
        line = _lead(r)["paragraphs"][0]
        assert line.startswith("GenomeVault does not answer whether to take ibuprofen")
        assert "flagged against four things" in line

        r = _ask(client, "Could pantoprazole work instead of omeprazole with my clopidogrel?")
        line = _lead(r)["paragraphs"][0]
        assert line.startswith("For clopidogrel, an entry is listed for clopidogrel with omeprazole")
        assert "for pantoprazole, an entry is listed for clopidogrel with pantoprazole" in line

        r = _ask(client, "Can I take St. John's wort with my medications?")
        line = _lead(r)["paragraphs"][0]
        assert "Nothing in your records is flagged with st johns wort" in line
        assert "GenomeVault has no entry for it with your medications" in line


def test_unknown_pair_no_data_line():
    from core.contracts import Answer
    from core.router import NO_DATA_TEXT
    p = appmod.load_profile()
    a = Answer(state="no_data", text=NO_DATA_TEXT, facts=[], sent_to_cloud=False)
    line = direct.direct_line("does pantoprazole interact with lisinopril", a, [], p)
    assert line == "Short answer: GenomeVault has no data on pantoprazole with lisinopril."


def test_other_questions_unchanged(client):
    with mock.patch.dict(os.environ, {"GV_DIRECT": "1"}):
        r = _ask(client, "what is the weather today")
    assert not any(s.get("direct") for s in r["sections"])


def test_every_line_passes_i7(client):
    with mock.patch.dict(os.environ, {"GV_DIRECT": "1"}):
        for q in EXAMPLES:
            r = _ask(client, q)
            lead = _lead(r)
            assert lead is not None and lead.get("direct"), q
            for para in lead["paragraphs"]:
                assert not wording_problems(para), (q, para, wording_problems(para))
                assert merge.guard(para).strip() == para.strip(), (q, para)
                assert "safe" not in para.lower()


def test_flag_off_byte_identical(client):
    for q in EXAMPLES:
        with mock.patch.dict(os.environ, {"GV_DIRECT": ""}):
            a = _ask(client, q)
        with mock.patch.dict(os.environ, {"GV_DIRECT": "0"}):
            b = _ask(client, q)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
        assert "direct" not in json.dumps(a)


def test_ledger_identical_on_and_off(client):
    """I3: the lead is composed locally; the ledger (what left the device) is the same with GV_DIRECT on or off."""
    def entries(q, flag):
        before = client.get("/api/ledger").json().get("entries", [])
        seq0 = max([e.get("seq", 0) for e in before] or [0])
        with mock.patch.dict(os.environ, {"GV_DIRECT": flag}):
            _ask(client, q)
        after = client.get("/api/ledger").json().get("entries", [])
        return [(e.get("kind"), e.get("bucket_id")) for e in after if e.get("seq", 0) > seq0 and e.get("kind") != "cover"]
    for q in EXAMPLES:
        assert entries(q, "") == entries(q, "1"), q


def test_direct_module_has_no_network():
    src = pathlib.Path(direct.__file__).read_text()
    for mod in ("httpx", "requests", "urllib", "socket", "aiohttp"):
        assert f"import {mod}" not in src and f"from {mod}" not in src
