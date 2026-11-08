"""BRIEF B queue 1: fixed bucket partition (I5, P6.5)."""
import json

from core.contracts import pair_key
from core.decoys import BUCKET_DIR, bucket_for, kind_of, load_buckets, universe

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
    raw = json.loads((BUCKET_DIR / "v1.json").read_text())
    assert raw["version"] == "v1" and raw["k"] == 8
    assert all(len(b.keys) == 8 for b in load_buckets("v1"))


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
    assert bucket_for("clopidogrel|esomeprazole") is None


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
