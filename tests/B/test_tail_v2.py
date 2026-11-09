"""tail-v2: tail-v1's keys grouped by frequency tier (D-040 part 2, D's E1 finding in D-017; I5)."""
import importlib.util
import json
import pathlib

from core.decoys import TAIL_VERSION, load_buckets

BUCKETS = pathlib.Path(__file__).resolve().parents[2] / "data" / "buckets"


def _builder():
    spec = importlib.util.spec_from_file_location("build_tail_v2", BUCKETS / "build_tail_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_tail_v2_is_current_reproducible_and_holds_tail_v1_keys():
    assert TAIL_VERSION == "tail-v2"
    committed = json.loads((BUCKETS / "tail-v2.json").read_text())
    assert _builder().build()["buckets"] == committed["buckets"]
    v1 = {k for b in load_buckets("tail-v1") for k in b.keys}
    v2 = [k for b in load_buckets("tail-v2") for k in b.keys]
    assert len(v2) == len(set(v2)) == len(v1) and set(v2) == v1
    assert all(len(b.keys) == 8 and b.id.startswith("tail-") for b in load_buckets("tail-v2"))


def test_tail_v2_statistical_attacker_near_one_in_eight():
    from eval.adaptive import attack_partition, tail_priors
    from eval.universe import load_universe
    u = load_universe()
    buckets = [list(b.keys) for b in load_buckets("tail-v2")]
    for unseen in ("smallest", "median"):   # tiering by unseen count makes both readings agree
        r = attack_partition(buckets, tail_priors(buckets, u, unseen=unseen))
        assert r["statistical"] <= 0.20 and r["stat_attacker_ceiling"] < 0.15, (unseen, r)
