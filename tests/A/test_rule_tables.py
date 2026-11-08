"""A queue 3: rule tables have exact keys, sources and tiers (F3, M4, I4, I6, I7)."""
import json
import pathlib
import re

import pytest

from core import rules
from core.contracts import pair_key

RULES = pathlib.Path(__file__).resolve().parents[2] / "data" / "rules"
VOCAB = {i.lower() for ings in json.loads((RULES / "drug_names.json").read_text())["names"].values() for i in ings}
LAB_TOKEN = re.compile(r"^[a-z]+$")


def _rules(name):
    return rules.tables()[name]["rules"]


def _all_rules():
    return [(name, r) for name in rules.TABLES for r in _rules(name)]


@pytest.mark.parametrize("name,rule", _all_rules(), ids=lambda x: x if isinstance(x, str) else x["id"])
def test_every_rule_has_source_tier_severity(name, rule):
    assert rule["tier"] == "curated"                         # I6: every local flag is curated
    assert rule["severity"] in {"high", "medium", "low"}
    assert isinstance(rule["needs_cloud"], bool)
    assert len(rule["source"]) > 10
    assert rule["text"] and "safe" not in rule["text"].lower()   # I7


def test_rule_ids_unique():
    ids = [r["id"] for _, r in _all_rules()]
    assert len(ids) == len(set(ids))


def test_gene_drug_keys_are_exact():
    for r in _rules("gene_drug"):
        assert r["key"] == rules.gene_drug_key(r["gene"], r["phenotype"], r["drug"], r["dose"])
        assert r["drug"] in VOCAB


def test_drug_drug_keys_are_sorted_pairs():
    for r in _rules("drug_drug"):
        a, b = r["drugs"]
        assert r["key"] == pair_key(a, b) and a != b
        assert {a, b} <= VOCAB


def test_drug_lab_keys_are_exact():
    for r in _rules("drug_lab"):
        assert r["key"] == rules.drug_lab_key(r["drug"], r["lab"], r["op"], r["value"])
        assert LAB_TOKEN.match(r["lab"]) and r["op"] in rules.OPS
        assert r["drug"] in VOCAB


def test_class_rules_only_listed_members():
    classes = rules.tables()["class_rules"]["classes"]
    for c in classes.values():
        assert set(c["members"]) <= VOCAB
    for r in _rules("class_rules"):
        assert len(r["classes"]) == 2 and all(c in classes for c in r["classes"])
    assert "aspirin" not in classes["nsaid"]["members"]


def test_keys_unique_across_tables():
    keys = [r["key"] for name in ("gene_drug", "drug_drug", "drug_lab") for r in _rules(name)]
    assert len(keys) == len(set(keys))


def test_pantoprazole_pair_absent():
    """S6 no-extrapolation demo: the exact pair is not in any table, including class expansions."""
    assert "clopidogrel|pantoprazole" not in rules.all_keys()


@pytest.mark.parametrize("key", ["aspirin|clopidogrel", "lisinopril|simvastatin", "amlodipine|simvastatin",
                                 "CYP2D6:normal_metabolizer|codeine", "CYP2C19:poor_metabolizer|citalopram"])
def test_keys_that_d_expects_offline_no_data_are_absent(key):
    """D's eval (Q03, Q05, Q08, Q09, Q10) expects these to be no_data locally."""
    assert key not in rules.all_keys()


def test_plan_keys_present_and_mapped():
    ids = rules.tables()["flag_ids"]
    assert set(ids) <= rules.all_keys()
    assert sorted(set(ids.values())) == ["X1", "X2", "X3", "X4", "X5"]
    assert {k for k, v in ids.items() if v == "X5"} == {
        "aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60"}
