"""D-040 part 5: typo set and long-tail E1. Both are reported apart from the core; with the dependency missing
they report 'skipped', and the safety checks run once A's suggest() and B's tail-v1.json are on the build."""
import json

import pytest

from eval import adaptive, run_all


def test_typo_set_is_twenty_and_independent_of_a():
    cases = json.loads(adaptive.TYPO_SET.read_text())["cases"]
    assert len(cases) == 20 and len({c["typed"] for c in cases}) == 20
    assert {c["meant"] for c in cases if c["group"] == "alex"} >= {"clopidogrel", "omeprazole", "simvastatin", "lisinopril", "aspirin"}
    a_typed = {"aspirn", "clopidogrl", "omeprazol", "simvastain", "lisinoprl", "plavicks", "ibuprophen"}
    assert not a_typed & {c["typed"] for c in cases}          # D's red-team set, not a copy of A's tests


def test_typos_zero_silent_wrong_substitutions():               # I4: never guess
    r = adaptive.run_typos()
    if r["status"] == "skipped":
        pytest.skip(r["reason"])
    assert r["silent_wrong"] == 0, [x for x in r["rows"] if x["silent_wrong"]]
    assert r["lookalike_assumed"] == 0, [x for x in r["rows"] if x["lookalike_assumed"]]
    assert r["correct"] >= 18


def test_tail_partition_attackers():                            # I5: a fixed partition, reported separately
    r = adaptive.run_tail()
    if r["status"] == "skipped":
        pytest.skip(r["reason"])
    assert r["status"] == "ran", r
    assert abs(r["repeat_ask"] - 0.125) < 0.05                   # fixed buckets: repeat asks reveal nothing more
    assert r["statistical"] <= r["stat_attacker_ceiling"] + 0.05


def test_attack_math_on_a_toy_partition():
    buckets = [[f"a{i}|x" for i in range(8)], [f"b{i}|y" for i in range(8)]]
    flat = {k: 1.0 for b in buckets for k in b}
    even = adaptive.attack_partition(buckets, flat, n=4000, seed=1)
    assert abs(even["repeat_ask"] - 0.125) < 0.03 and abs(even["statistical"] - 0.125) < 0.03
    skew = dict(flat, **{"a0|x": 93.0, "b0|y": 93.0})            # one common pair per bucket: the statistical attacker wins
    s = adaptive.attack_partition(buckets, skew, n=4000, seed=1)
    assert s["statistical"] > 0.9 and abs(s["stat_attacker_ceiling"] - 0.93) < 0.01


def test_adaptive_section_never_touches_core_numbers():
    md = run_all.write_adaptive({"typos": {"status": "skipped", "reason": "x"}, "tail": {"status": "skipped", "reason": "y"}})
    assert "Not run: x." in md and "Not run: y." in md and "numbers.md" in md
