"""BRIEF B queue 1: fixed bucket partition (I5, P6.5)."""
import json

from core.contracts import pair_key
from core.decoys import BUCKET_DIR, CURRENT_VERSION, bucket_for, kind_of, load_buckets, universe

# Alex's flag keys (mocks/flags.json, P5 X1-X4) plus the drug pairs the demo can ask about.
ALEX_KEYS = [
    "CYP2C19:poor_metabolizer|clopidogrel",
    "clopidogrel|omeprazole",
    "SLCO1B1:decreased_function|simvastatin|dose>20mg",
    "lisinopril|potassium>5.0",
    "aspirin|ibuprofen",
    "clopidogrel|ibuprofen",
    "ibuprofen|lisinopril",
    "clopidogrel|pantoprazole",
]


def test_file_is_valid_and_versioned():
    for v in ("v1", "v2", "v3"):
        raw = json.loads((BUCKET_DIR / f"{v}.json").read_text())
        assert raw["version"] == v and raw["k"] == 8
        assert all(len(b.keys) == 8 and b.version == v for b in load_buckets(v))


def test_current_version_is_v3():
    assert CURRENT_VERSION == "v3"
    assert {b.version for b in load_buckets()} == {"v3"}


def test_old_versions_still_load_unchanged():
    # Old versions are frozen (I5): v1 keeps 12 buckets / 96 keys, v2 keeps 14 / 112.
    assert len(load_buckets("v1")) == 12 and len(universe("v1")) == 96
    assert len(load_buckets("v2")) == 14 and len(universe("v2")) == 112


# Every exact key A's rule tables can emit (rules.all_keys() on PR #1 @ 6e484af, A-003).
A_RULE_KEYS = [
    "CYP2C19:intermediate_metabolizer|clopidogrel", "CYP2C19:poor_metabolizer|clopidogrel",
    "SLCO1B1:decreased_function|simvastatin|dose>20mg", "SLCO1B1:poor_function|simvastatin",
    "aspirin|celecoxib", "aspirin|ibuprofen", "aspirin|naproxen", "celecoxib|clopidogrel",
    "celecoxib|lisinopril", "celecoxib|prasugrel", "celecoxib|ticagrelor", "clopidogrel|esomeprazole",
    "clopidogrel|ibuprofen", "clopidogrel|naproxen", "clopidogrel|omeprazole", "ibuprofen|egfr<60",
    "ibuprofen|lisinopril", "ibuprofen|prasugrel", "ibuprofen|ticagrelor", "lisinopril|naproxen",
    "lisinopril|potassium>5.0", "naproxen|prasugrel", "naproxen|ticagrelor", "spironolactone|potassium>5.0",
]


def test_v3_keeps_v2_and_covers_every_rule_key():
    v3 = set(universe("v3"))
    assert set(universe("v2")) <= v3
    assert len(v3) == 136 and len(load_buckets("v3")) == 17
    for k in A_RULE_KEYS:
        assert bucket_for(k) is not None, k


def test_rule_keys_match_real_rules_when_present():
    # After G1 merges A's rules.py, the universe must still cover everything it can emit.
    try:
        from core import rules  # type: ignore
    except ImportError:
        return
    missing = sorted(k for k in rules.all_keys() if bucket_for(k) is None)
    assert not missing, missing


def test_v2_keeps_every_v1_key_and_adds_question_keys():
    v2 = set(universe("v2"))
    assert set(universe("v1")) <= v2
    assert len(v2) == 112
    # Keys D's scripted questions need (Q05, Q12/Q20, Q14), in A's spelling.
    for k in ("CYP2C19:poor_metabolizer|citalopram", "lisinopril|egfr<60", "simvastatin|alt>120"):
        assert bucket_for(k) is not None, k


def _drug_of(key):
    parts = key.split("|")
    return parts[1] if kind_of(key) == "gene_drug" else parts[0]


def test_no_drug_twice_in_gene_or_lab_bucket():
    # Two warfarin genes in one bucket would reveal "warfarin" (D-006 spirit).
    for b in load_buckets("v2") + load_buckets():
        if kind_of(b.keys[0]) != "drug_drug":
            drugs = [_drug_of(k) for k in b.keys]
            assert len(drugs) == len(set(drugs)), b.id


def test_drug_at_most_twice_in_pair_bucket():
    for b in load_buckets("v2") + load_buckets():
        if kind_of(b.keys[0]) == "drug_drug":
            drugs = [d for k in b.keys for d in k.split("|")]
            assert max(drugs.count(d) for d in drugs) <= 2, b.id


def test_universe_at_least_64_and_partition():
    keys = universe()
    assert len(keys) >= 64
    assert len(keys) == len(set(keys)), "every key in exactly one bucket"
    for k in keys:
        assert bucket_for(k).keys.count(k) == 1


def test_every_member_maps_to_same_bucket():
    for b in load_buckets():
        assert {bucket_for(k).id for k in b.keys} == {b.id}


def test_alex_keys_and_pantoprazole_present():
    for k in ALEX_KEYS:
        assert bucket_for(k) is not None, k


def test_unknown_key_has_no_bucket():
    assert bucket_for("clopidogrel|st_johns_wort") is None  # D Q16: outside the universe


def test_drug_pairs_are_canonical():
    for k in universe():
        if kind_of(k) == "drug_drug":
            a, b = k.split("|")
            assert k == pair_key(a, b), k


def test_buckets_are_one_key_family():
    for b in load_buckets():
        assert len({kind_of(k) for k in b.keys}) == 1, b.id


def test_keys_sorted_within_bucket():
    # Position in the bucket must not hint at which member is real.
    for b in load_buckets():
        assert b.keys == sorted(b.keys), b.id


def test_omeprazole_and_pantoprazole_in_different_buckets():
    # S6 no-extrapolation beat: the pantoprazole key must not be pre-filled by the omeprazole send.
    assert bucket_for("clopidogrel|omeprazole").id != bucket_for("clopidogrel|pantoprazole").id


def test_at_most_two_alex_drug_pairs_per_bucket():
    meds = {"aspirin", "clopidogrel", "omeprazole", "simvastatin", "lisinopril", "ibuprofen", "pantoprazole"}
    for b in load_buckets():
        alex = [k for k in b.keys if kind_of(k) == "drug_drug" and set(k.split("|")) <= meds]
        assert len(alex) <= 2, (b.id, alex)
