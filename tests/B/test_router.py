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


def test_alias_variant_gets_member_answer_from_the_same_bucket():
    # I3 (v5): the intermediate-metabolizer variant leaves in the same bucket as the poor-metabolizer one,
    # with the same 8 texts, and its answer is stored under its own key. A later poor-metabolizer
    # question is then a KB hit and nothing is sent.
    im = X1.model_copy(update={"id": "X1b", "key": "CYP2C19:intermediate_metabolizer|clopidogrel"})
    a = router.route("Does my genetics change how clopidogrel works for me?", [im])
    assert a.state == "known" and a.sent_to_cloud and [f.key for f in a.facts] == [im.key]
    [e] = ledger.feed(0)
    assert e.bucket_id == bucket_for(X1.key).id and len(ledger.outbound(e.seq)) == 8
    b = router.route("Does my genetics change how clopidogrel works for me?", [X1])
    assert b.state == "known" and not b.sent_to_cloud
    assert a.facts[0].text == b.facts[0].text


# I4: a question no flag covers is never "checked, nothing found" (D, 20261108-1438) -------------------

CR = Flag(id="CR-001", key="aspirin|naproxen", severity="high", engine="class_rule",
          evidence=["NSAID + antiplatelet"], needs_cloud=False)


@pytest.fixture
def cache_all(tmp_path, monkeypatch):
    from core.decoys import load_buckets
    d = tmp_path / "all"
    d.mkdir()
    for b in load_buckets():
        (d / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("GV_CLOUD_CACHE", str(d))


def test_no_flag_out_of_partition_is_no_data():
    a = router.route("Can I take St. John's wort with my medications?", [])
    assert a.state == "no_data" and not a.sent_to_cloud and a.facts == []
    assert [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_gene_question_without_flag_is_sent_online(cache_all):
    a = router.route("Would my genes matter if I ever needed warfarin?", [])
    assert a.state == "known" and a.sent_to_cloud
    assert {f.key for f in a.facts} == {"CYP2C9:poor_metabolizer|warfarin", "VKORC1:high_sensitivity|warfarin"}
    assert all(e.personal_fields_sent == 0 for e in ledger.feed(0))


def test_gene_question_without_flag_offline_is_no_data(monkeypatch):
    monkeypatch.delenv("DEMO")
    a = router.route("If I'm prescribed citalopram for anxiety, could my genes affect it?", [])
    assert a.state == "no_data" and not a.sent_to_cloud and a.text == router.OFFLINE_TEXT


def test_unassessed_gene_drug_is_no_data():
    a = router.route("Would my genes affect codeine?", [])     # CYP2D6 not_assessed, out of partition (D-021)
    assert a.state == "no_data" and not a.sent_to_cloud


def test_lab_question_uses_flag_drug_and_is_not_covered_by_x3(cache_all, monkeypatch):
    a = router.route("Are my liver tests a problem for my statin?", [X3])
    assert a.state == "known" and [f.key for f in a.facts] == ["simvastatin|alt>120"]
    ledger.reset()
    kb.reset()
    monkeypatch.delenv("DEMO")
    b = router.route("Does my CK level matter for my simvastatin?", [X3])
    assert b.state == "no_data" and not b.sent_to_cloud      # X3 is shown, but the CK topic itself is open


def test_covering_class_rule_flag_is_known_even_with_out_of_partition_pair(monkeypatch):
    monkeypatch.delenv("DEMO")
    a = router.route("What about naproxen instead of ibuprofen?", [CR])
    assert a.state == "known" and a.text == router.LOCAL_TEXT and not a.sent_to_cloud


def test_flag_for_another_drug_does_not_cover_the_question():
    a = router.route("Can I take zolpidem?", [X3])            # names zolpidem only: X3 says nothing about it
    assert a.state == "no_data" and not a.sent_to_cloud


def test_brand_names_count_as_their_ingredient():
    # A's normalize reads brands (B-019): "Plavix with Protonix" is clopidogrel|pantoprazole, not "no drug named".
    assert router._question_keys("Is Plavix OK with Protonix?") == ["clopidogrel|pantoprazole"]
    assert router._named_drugs("Can I take Advil with my lisinopril?") == ["ibuprofen", "lisinopril"]


def test_brand_question_is_not_covered_by_an_unrelated_flag_offline(monkeypatch):
    # I4: a local clopidogrel flag shares a drug, but the asked pair clopidogrel|pantoprazole is open.
    local = Flag(id="X2", key="aspirin|clopidogrel", severity="medium", engine="drug_drug",
                 evidence=["aspirin with clopidogrel"], needs_cloud=False)
    monkeypatch.delenv("DEMO")
    a = router.route("Is Plavix OK with Protonix?", [local])
    assert a.state == "no_data" and not a.sent_to_cloud and a.text == router.OFFLINE_TEXT


def test_brand_question_gets_the_exact_pair_fact_online(cache_all):
    a = router.route("Is Plavix OK with Protonix?", [])
    assert a.state == "known" and a.sent_to_cloud
    assert [f.key for f in a.facts] == ["clopidogrel|pantoprazole"]
    assert all(e.personal_fields_sent == 0 for e in ledger.feed(0))


# A cloud flag for another drug is neither fetched nor quoted (I4) ------------------------------------

def test_unrelated_cloud_flag_is_not_sent_or_quoted():
    # Alex's X1 (clopidogrel) is in context, but the question is about simvastatin: X3 answers it
    # locally, nothing leaves, and no clopidogrel text appears in the answer.
    a = router.route("Is simvastatin affected by my genes?", [X1, X3])
    assert a.state == "known" and a.text == router.LOCAL_TEXT and a.facts == []
    assert not a.sent_to_cloud and [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_unrelated_cloud_flag_already_in_kb_is_not_quoted():
    router.route("clopidogrel?", [X1])                          # X1's answer is now in the KB
    ledger.reset()
    a = router.route("Can I take zolpidem?", [X1])
    assert a.state == "no_data" and a.facts == [] and not a.sent_to_cloud


def test_question_naming_no_drug_still_uses_every_flag():
    a = router.route("Anything I should ask my pharmacist about?", [X1, X3])
    assert a.state == "known" and [f.key for f in a.facts] == [X1.key]
