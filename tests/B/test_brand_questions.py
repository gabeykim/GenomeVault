"""Brand names in a question ("Advil with my Plavix?", "Prilosec", "Zestril and Aleve").

The router asks the cloud about the ingredient pair only, through A's real normalizer, which is on main.
No brand string, no question text and no personal field may leave the device (I3). The pair the user
named must be the exact key fetched and must lead Answer.facts (I4, B-026).
"""
import json

import pytest

from core import kb, ledger, router
from core.decoys import load_buckets

BRAND_QUESTIONS = [
    ("Can I take Advil with my Plavix?", "clopidogrel|ibuprofen", ["advil", "plavix"]),
    ("Is Prilosec OK with Plavix?", "clopidogrel|omeprazole", ["prilosec", "plavix"]),
    ("Plavix with Protonix?", "clopidogrel|pantoprazole", ["plavix", "protonix"]),
    ("Is Zestril ok with Aleve?", "lisinopril|naproxen", ["zestril", "aleve"]),
    ("Bayer low dose with Plavix?", "aspirin|clopidogrel", ["bayer", "plavix"]),
]


@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(router.cloud, "_forced", None)
    for b in load_buckets():
        (tmp_path / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


def _outbound() -> list[str]:
    return [t for e in ledger.feed(0) for t in ledger.outbound(e.seq)]


@pytest.mark.parametrize("q,key,brands", BRAND_QUESTIONS)
def test_brand_question_maps_to_ingredient_key(q, key, brands):
    assert router._question_keys(q) == [key]


@pytest.mark.parametrize("q,key,brands", BRAND_QUESTIONS)
def test_brand_question_sends_no_brand_or_question(q, key, brands):
    a = router.route(q, [])
    assert a.sent_to_cloud
    assert all(e.personal_fields_sent == 0 for e in ledger.feed(0))
    sent = " ".join(_outbound()).lower()
    assert sent
    for brand in brands:
        assert brand not in sent
    assert q.lower() not in sent


@pytest.mark.parametrize("q,key,brands", BRAND_QUESTIONS)
def test_brand_question_answer_leads_with_named_pair(q, key, brands):
    a = router.route(q, [])
    assert a.facts and a.facts[0].key == key


@pytest.mark.parametrize("q,key,brands", BRAND_QUESTIONS)
def test_brand_question_repeat_is_local(q, key, brands):
    router.route(q, [])
    before = len(ledger.feed(0))
    a = router.route(q, [])
    assert not a.sent_to_cloud
    assert all(e.bytes_out == 0 for e in ledger.feed(0)[before:])


def test_brand_and_ingredient_spellings_send_identical_traffic():
    router.route("Can I take Advil with my Plavix?", [])
    brand = _outbound()
    ledger.reset()
    kb.reset()
    router.route("Can I take ibuprofen with my clopidogrel?", [])
    assert sorted(brand) == sorted(_outbound())
