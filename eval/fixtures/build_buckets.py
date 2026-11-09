"""One-off generator for D's STAND-IN bucket partition (eval/fixtures/buckets_v1.json).

Run once, offline, and commit the output: `python -m eval.fixtures.build_buckets`.
The output is a fixed, versioned partition (I5). Nothing here ever runs on a real query.
B owns the real partition (data/buckets/v1.json); evals switch to it automatically when it exists.

Design, as a good-faith guess at what B will ship:
1. No bucket holds more than 2 keys from any one co-prescription cluster (D-006: spread clusters).
2. Among seeded shuffles meeting (1), keep the one with the lowest statistical-attacker success,
   sum over buckets of max(prior) / total prior (1/8 is the floor, reached when priors are equal within each bucket).
"""
import json
import random

from eval.universe import FIXTURE_BUCKETS, load_universe

K, SEEDS = 8, 5000


def score(buckets, prior):
    total = sum(prior.values())
    return sum(max(prior[k] for k in b) for b in buckets) / total


def ok(buckets, clusters):
    return all(sum(k in b for k in c) <= 2 for b in buckets for c in clusters.values())


def build():
    u = load_universe()
    keys = sorted(k for k, v in u.keys.items() if v.get("src", "d-v1") == "d-v1")   # the stand-in stays D's original 64
    assert len(keys) % K == 0, f"universe size {len(keys)} must be a multiple of {K}"
    prior = {k: u.prior(k) for k in keys}
    clusters = {c: [k for k in ks if k in prior] for c, ks in u.clusters.items()}
    best = None
    for seed in range(SEEDS):
        rng = random.Random(seed)
        # frequency-banded start (similar priors together), then shuffle within +-1 band for diversity
        order = sorted(keys, key=lambda k: (-prior[k] + rng.uniform(-2.5, 2.5)))
        buckets = [order[i:i + K] for i in range(0, len(order), K)]
        if not ok(buckets, clusters):
            continue
        s = score(buckets, prior)
        if best is None or s < best[0]:
            best = (s, seed, buckets)
    if best is None:
        raise SystemExit("no partition met the cluster constraint")
    s, seed, buckets = best
    out = {"version": "fixture-v1", "doc": f"D stand-in partition (build_buckets.py, seed {seed}, stat-attacker score {s:.3f}). Replace with B's data/buckets/v1.json.",
           "buckets": [{"id": f"B{i:02d}", "keys": sorted(b)} for i, b in enumerate(buckets)]}
    FIXTURE_BUCKETS.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {FIXTURE_BUCKETS} seed={seed} score={s:.3f}")


if __name__ == "__main__":
    build()
