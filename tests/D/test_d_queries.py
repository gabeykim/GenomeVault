"""D queue item 1: the 20 scripted questions and the stand-in universe/partition are well formed."""
from collections import Counter

from core.contracts import Bucket, pair_key
from core.interfaces import load_profile
from eval.universe import generalize_key, load_partition, load_queries, load_universe

QUERIES = load_queries()
STATES = {"known", "none_listed", "no_data"}


def test_twenty_questions_in_plan_mix():
    assert len(QUERIES) == 20
    assert Counter(q["category"] for q in QUERIES) == {
        "gene_drug": 5, "drug_drug": 5, "drug_lab": 4, "otc": 3, "open_ended": 3}
    assert len({q["id"] for q in QUERIES}) == 20


def test_fields_and_states():
    for q in QUERIES:
        assert q["expected_state"] in STATES and q["offline_state"] in STATES, q["id"]
        assert set(q["expected_flags"]) <= {"X1", "X2", "X3", "X4", "X5"}, q["id"]
        assert isinstance(q["needs_cloud"], bool) and isinstance(q["in_universe"], bool)
        if q["topic_keys"]:
            assert len(q["topic_keys"]) == len(q["keys"]), q["id"]


def test_drug_pair_keys_are_canonical():
    for q in QUERIES:
        if q["category"] == "drug_drug":
            for k in q["keys"]:
                a, b = k.split("|")
                assert pair_key(a, b) == k, k


def test_topic_keys_are_generalized_local_keys():
    for q in QUERIES:
        for k, t in zip(q["keys"], q["topic_keys"]):
            assert generalize_key(k) == t, (q["id"], k, t)


def test_topic_keys_hold_nothing_personal():
    p = load_profile()
    personal = set(p.genotypes.values()) | set(p.phenotypes.values()) | {str(l.value) for l in p.labs}
    for q in QUERIES:
        for t in q["topic_keys"]:
            assert not any(v in t for v in personal), (q["id"], t)
            assert ">" not in t and "<" not in t and ":" not in t, t


def test_never_safe_never_start_stop():                     # I7
    for q in QUERIES:
        r = q["reference"].lower()
        assert " safe" not in f" {r}", q["id"]
        assert "stop taking" not in r and "start taking" not in r, q["id"]


def test_demo_beats_covered():
    ids = {q["id"]: q for q in QUERIES}
    assert ids["Q07"]["keys"] == ["clopidogrel|pantoprazole"] and ids["Q07"]["offline_state"] == "no_data"   # S6 no-extrapolation
    assert "X5" in ids["Q15"]["expected_flags"] and ids["Q15"]["offline_state"] == "known"                    # S6 offline ibuprofen
    assert set(ids["Q18"]["expected_flags"]) == {"X1", "X2", "X3", "X4"}                                       # S4


def test_universe_membership_matches_partition():
    part = load_partition(prefer_real=False)
    for q in QUERIES:
        if q["topic_keys"]:
            inside = all(part.bucket_for(t) is not None for t in q["topic_keys"])
            assert inside == q["in_universe"], q["id"]


def test_fixture_partition_is_valid():                     # I5
    part = load_partition(prefer_real=False)
    u = load_universe()
    assert len(part.buckets) * 8 == len(part.keys) == len(u.keys) >= 64
    for b in part.buckets:
        Bucket.model_validate(b.model_dump())
    for k in ["CYP2C19|clopidogrel", "clopidogrel|omeprazole", "SLCO1B1|simvastatin", "lisinopril|potassium", "clopidogrel|pantoprazole"]:
        assert part.bucket_for(k) is not None, k
    for name, cluster in u.clusters.items():
        assert all(k in u.keys for k in cluster), name
        for b in part.buckets:
            assert sum(k in b.keys for k in cluster) <= 2, (name, b.id)


def test_generalize_examples():
    assert generalize_key("CYP2C19:poor_metabolizer|clopidogrel") == "CYP2C19|clopidogrel"
    assert generalize_key("SLCO1B1:decreased_function|simvastatin|dose>20mg") == "SLCO1B1|simvastatin"
    assert generalize_key("lisinopril|potassium>5.0") == "lisinopril|potassium"
    assert generalize_key("omeprazole|clopidogrel") == "clopidogrel|omeprazole"
