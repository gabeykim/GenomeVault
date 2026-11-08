import json

import pytest

from core import kb, ledger, router
from core.contracts import Flag
from core.decoys import bucket_for
from core.interfaces import load_profile
from core.validator import check_outbound, check_output

X1 = Flag(id="X1", key="CYP2C19:poor_metabolizer|clopidogrel", severity="high", engine="gene_drug",
          evidence=["CYP2C19 poor metabolizer"], needs_cloud=True)
X3 = Flag(id="X3", key="SLCO1B1:decreased_function|simvastatin|dose>20mg", severity="medium",
          engine="gene_drug", evidence=["simvastatin 40 mg"], needs_cloud=False)
ALLERGY = Flag(id="A1", key="penicillin|amoxicillin", severity="high", engine="allergy",
               evidence=["penicillin allergy"], needs_cloud=True)


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    """DEMO=1 replay from a cache that answers every key of X1's bucket."""
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(router.cloud, "_forced", None)
    b = bucket_for(X1.key)
    (tmp_path / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


def test_local_only_when_no_flag_needs_cloud():
    a = router.route("Is my simvastatin dose a problem?", [X3])
    assert a.state == "known" and not a.sent_to_cloud
    [e] = ledger.feed(0)
    assert e.kind == "local_only" and e.bytes_out == 0


def test_allergy_flags_never_leave():
    a = router.route("What about amoxicillin?", [ALLERGY])
    assert not a.sent_to_cloud
    assert [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_one_question_end_to_end_sends_whole_bucket():
    a = router.route("Does my genetics change how clopidogrel works for me?", [X1])
    assert a.state == "known" and a.sent_to_cloud
    assert [f.key for f in a.facts] == [X1.key]
    assert all(f.tier == "cloud" for f in a.facts)
    [e] = ledger.feed(0)
    assert e.kind == "bucket" and e.bucket_id == bucket_for(X1.key).id
    assert e.bytes_out > 0 and e.personal_fields_sent == 0
    texts = ledger.outbound(e.seq)
    assert len(texts) == 8                                   # all 8 members leave (I5)
    assert check_outbound(texts, load_profile(), allow=["clopidogrel"])
    assert check_output(a.text, a.facts)


def test_question_text_never_leaves():
    q = "I am 58, CYP2C19 *2/*2, eGFR 48 - clopidogrel?"
    router.route(q, [X1])
    [e] = ledger.feed(0)
    for t in ledger.outbound(e.seq):
        assert q not in t and "58" not in t and "*2" not in t


def test_leak_blocks_whole_bucket(monkeypatch):
    real = router.topic_for_key
    monkeypatch.setattr(router, "topic_for_key",
                        lambda k: real(k).model_copy(update={"text": real(k).text + " eGFR 48"}))
    a = router.route("clopidogrel?", [X1])
    assert not a.sent_to_cloud and a.state == "no_data"
    [e] = ledger.feed(0)
    assert e.kind == "blocked" and e.bytes_out == 0


def test_key_outside_universe_is_no_data_and_sends_nothing():
    odd = Flag(id="Z", key="madeupdrug|otherdrug", severity="low", engine="drug_drug",
               evidence=[], needs_cloud=True)
    a = router.route("?", [odd])
    assert a.state == "no_data" and not a.sent_to_cloud
    assert ledger.feed(0) == []


def test_missing_cache_entry_is_no_data_not_invented(tmp_path, monkeypatch):
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path / "empty"))
    a = router.route("clopidogrel?", [X1])
    assert a.state == "no_data" and a.facts == []
    assert a.sent_to_cloud                                     # the bucket did leave; it just had no answer


def test_offline_sends_nothing(monkeypatch):
    monkeypatch.delenv("DEMO")
    a = router.route("clopidogrel?", [X1])
    assert a.state == "no_data" and not a.sent_to_cloud
    assert ledger.feed(0) == []


def test_question_names_pair_directly():
    keys = router._question_keys("Can I take pantoprazole with clopidogrel instead?")
    assert keys == ["clopidogrel|pantoprazole"]


def test_same_bucket_sent_once():
    b = bucket_for(X1.key)
    other = next(k for k in b.keys if k != X1.key)
    f2 = Flag(id="Y", key=other, severity="low", engine="gene_drug", evidence=[], needs_cloud=True)
    a = router.route("?", [X1, f2])
    assert [e.kind for e in ledger.feed(0)] == ["bucket"]
    assert {f.key for f in a.facts} == {X1.key, other}
