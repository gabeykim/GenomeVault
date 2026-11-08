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
    d_keys = {k for k, v in u.keys.items() if v.get("src", "d-v1") == "d-v1"}
    assert len(part.buckets) * 8 == len(part.keys) == len(d_keys) >= 64 and set(part.keys) == d_keys
    for b in part.buckets:
        Bucket.model_validate(b.model_dump())
    for k in ["CYP2C19|clopidogrel", "clopidogrel|omeprazole", "SLCO1B1|simvastatin", "lisinopril|potassium", "clopidogrel|pantoprazole"]:
        assert part.bucket_for(k) is not None, k
    for name, cluster in u.clusters.items():
        assert all(k in u.keys for k in cluster), name
        for b in part.buckets:
            assert sum(k in b.keys for k in cluster) <= 2, (name, b.id)
    assert all(any(k in c for c in u.clusters.values()) for k in u.keys)     # every key belongs to a scenario


def test_generalize_examples():
    assert generalize_key("CYP2C19:poor_metabolizer|clopidogrel") == "CYP2C19|clopidogrel"
    assert generalize_key("SLCO1B1:decreased_function|simvastatin|dose>20mg") == "SLCO1B1|simvastatin"
    assert generalize_key("lisinopril|potassium>5.0") == "lisinopril|potassium"
    assert generalize_key("omeprazole|clopidogrel") == "clopidogrel|omeprazole"


def _localize(key: str) -> str:
    """Turn a generalized fixture key into B's exact-key spelling (phenotype / threshold added)."""
    parts = key.split("|")
    if parts[0].isupper():
        return f"{parts[0]}:poor_metabolizer|" + "|".join(parts[1:])
    if parts[-1] in ("potassium", "egfr", "alt", "ck", "inr", "sodium"):
        return "|".join(parts[:-1]) + f"|{parts[-1]}>1.0"
    return key


def test_loads_exact_key_partition_like_b(tmp_path):     # B-001 keys carry phenotype / threshold
    import json
    fixture = load_partition(prefer_real=False)
    raw = {"version": "v1", "buckets": [{"id": b.id, "keys": [_localize(k) for k in b.keys]} for b in fixture.buckets]}
    f = tmp_path / "v1.json"
    f.write_text(json.dumps(raw))
    part = load_partition(path=f)
    assert part.source.startswith("real") and set(part.keys) == set(fixture.keys)
    assert part.stats["raw_keys_with_phenotype"] > 0 and part.stats["partition_keys_without_prior"] == 0
    assert part.bucket_for("CYP2C19|clopidogrel").id == fixture.bucket_for("CYP2C19|clopidogrel").id


def test_falls_back_when_partition_does_not_overlap(tmp_path):
    import json
    raw = [{"id": f"x{i}", "keys": [f"drug{i}{j}|other{i}{j}" for j in range(8)]} for i in range(8)]
    f = tmp_path / "v1.json"
    f.write_text(json.dumps(raw))
    part = load_partition(path=f)
    assert part.source.startswith("fixture") and "fallback_reason" in part.stats


def test_generalize_b_spellings():
    assert generalize_key("HLA-B:5701_positive|abacavir") == "HLA-B|abacavir"
    assert generalize_key("sotalol|magnesium<1.7") == "sotalol|magnesium"
    assert generalize_key("ibuprofen|egfr<60") == "ibuprofen|egfr"


def test_priors_cover_every_key_in_bs_v1_partition():   # B-001 keys, D-005
    import json, pathlib
    b_keys = json.loads((pathlib.Path(__file__).parent / "b_v1_keys.json").read_text())
    u = load_universe()
    assert len(b_keys) == 96 and all(generalize_key(k) in u.keys for k in b_keys)


def test_expected_state_follows_loaded_partition(tmp_path):
    import json
    from eval.backends import SimBackend, expected_state
    q09 = next(q for q in QUERIES if q["id"] == "Q09")
    fixture = load_partition(prefer_real=False)
    assert expected_state(q09, fixture) == "no_data" and SimBackend(fixture).ask(q09).cloud_calls == 0
    keys = sorted(fixture.keys)
    keys[0] = "lisinopril|simvastatin"                     # a partition that contains Q09's pair
    raw = [{"id": f"b{i:02d}", "keys": keys[i * 8:(i + 1) * 8]} for i in range(len(keys) // 8)]
    f = tmp_path / "v1.json"
    f.write_text(json.dumps(raw))
    part = load_partition(path=f)
    assert expected_state(q09, part) == "known" and SimBackend(part).ask(q09).cloud_calls == 1
