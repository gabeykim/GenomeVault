"""D queue items 2-3: red team conditions, attackers and charts behave as the PLAN predicts. Offline, deterministic."""
import pathlib
import random
import re
import xml.etree.ElementTree as ET

import pytest

from eval import attackers as A
from eval import transport as T
from eval.charts import grouped_bars, line_chart
from eval.redteam import run
from eval.synth import alex, make_patients
from eval.universe import load_partition, load_universe, priors_for

PART, U = load_partition(prefer_real=False), load_universe()
PRIORS = priors_for(PART, U)


@pytest.fixture(scope="module")
def res():
    return run(trials=200, asks=3, seed=11, write=False)


def test_naive_leaks_everything(res):
    n = res["single_topic"]["naive"]
    assert n["intersection"] == n["statistical"] == 1.0 and n["genotype_leaked"] == 1.0


def test_random_decoys_fail_on_repeat(res):                 # D-003
    assert res["single_topic"]["random_decoys"]["intersection"] >= 0.85


def test_fixed_buckets_near_one_in_eight(res):              # I5, E1 target
    fb = res["single_topic"]["fixed_buckets"]
    assert 0.06 <= fb["intersection"] <= 0.22
    assert fb["genotype_leaked"] == 0.0


def test_statistical_attacker_bounded_by_design_ceiling(res):
    fb = res["single_topic"]["fixed_buckets"]
    assert fb["statistical"] <= res["bucket_design"]["stat_attacker_ceiling"] + 0.12
    assert res["single_topic"]["random_decoys_1ask"]["statistical"] > fb["statistical"] - 0.05


def test_fixed_bucket_is_identical_every_ask():
    p = make_patients(1, 3, U, PART)[0]
    t = T.fixed_buckets(p, PART, random.Random(0), asks=5)
    assert len({tuple(r.topics) for r in t.requests()}) == 1


def test_out_of_universe_sends_nothing():
    p = alex(["lisinopril|simvastatin"])
    assert T.fixed_buckets(p, PART, random.Random(0)).requests() == []


def test_no_personal_fields_outside_naive():                # I3, checked on the simulated wire
    p = alex(["CYP2C19|clopidogrel", "lisinopril|potassium"])
    personal = set(p.genotypes.values()) | {str(v) for v in p.labs.values()} | {"58"}
    for t in (T.random_decoys(p, PART, random.Random(1)), T.fixed_buckets(p, PART, random.Random(1), 2, True, 2)):
        wire = str(t.visible())
        assert not any(v in wire for v in personal)


def test_separate_sessions_and_cover_reduce_joint_inference(res):   # D-006
    j = res["joint"]
    assert j["same_session"]["scenario"] > j["separate_cover_linkable"]["scenario"]
    assert j["same_session"]["key_recall"] > j["separate_cover_unlinkable"]["key_recall"]


def test_deterministic():
    a, b = run(trials=30, seed=5, write=False), run(trials=30, seed=5, write=False)
    assert a["single_topic"] == b["single_topic"] and a["joint"]["same_session"] == b["joint"]["same_session"]


def test_charts_are_valid_svg():
    for svg in (grouped_bars("t", "s", ["a", "b"], [("x", [0.5, 0.1]), ("y", [0.2, None])], y_max=1, pct=True, ref=(0.125, "1/8")),
                line_chart("t", "s", ["1", "2", "3"], [("x", [0.1, 0.5, 0.9])])):
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")


def test_only_llm_client_may_call_models():                 # I2 for eval/
    net = re.compile(r"^\s*(import|from)\s+(anthropic|openai|requests|httpx|urllib3|aiohttp|socket|urllib\.request|http\.client)\b", re.M)
    for f in (pathlib.Path(__file__).resolve().parents[2] / "eval").rglob("*.py"):
        if f.name != "llm_client.py":
            assert not net.search(f.read_text()), f


def test_llm_client_replay_only(monkeypatch, tmp_path):
    from eval import llm_client as L
    monkeypatch.setattr(L, "CACHE", tmp_path)
    monkeypatch.setenv("EVAL_REPLAY", "1")
    with pytest.raises(L.LLMUnavailable):
        L.complete("hello")
    L._cache_put(L._key(L.model_name(), "", "hi"), L.model_name(), 'ok {"real_topics": ["a|b"]}')
    assert L.complete_json("hi") == {"real_topics": ["a|b"]}
