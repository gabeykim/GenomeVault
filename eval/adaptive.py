"""D-040 part 5: evaluations for adaptive questions. Both parts are reported separately from the core numbers and
change no gate check, so the figures already quoted on the slides stay as they are until the integrator confirms D-040.

1. Typos: D's own 20-item set (`eval/fixtures/typo_set.json`) against A's `core.normalize.suggest` with GV_FUZZY=1.
   Correct = the intended name is among the choices. Unsafe = a silent wrong substitution (mode "assumed" and the
   assumed name is a different ingredient from the intended one), or a look-alike name that was assumed instead of
   asked. Both unsafe counts must be 0 (I4: never guess).
2. Long tail: the repeat-ask and statistical attackers on B's second fixed partition `data/buckets/tail-v1.json`
   (I5). Its buckets are a seeded shuffle with no frequency balancing, so the statistical attacker is expected to do
   better than on the core. Tail pairs have no priors of their own: each drug's synthetic frequency is the sum of its
   priors in D's universe file, a pair's is the product of its two drugs', and an unseen drug or lab gets the
   smallest known frequency. These are illustrative, like the core's priors, not prescribing data.

Each part reports `status: "skipped"` with the reason when its dependency is not on this build. Run:
python -m eval.adaptive"""
from __future__ import annotations

import json
import os
import random
from collections import defaultdict

from eval.universe import ROOT, load_universe

RESULTS = ROOT / "eval" / "results"
TYPO_SET = ROOT / "eval" / "fixtures" / "typo_set.json"
TAIL_FILE = ROOT / "data" / "buckets" / "tail-v1.json"


def _ingredients(normalize, name: str) -> set[str]:
    return {d.ingredient for d in normalize.to_ingredients(name)}


def run_typos() -> dict:
    try:
        from core import normalize
    except ImportError as e:                                   # pragma: no cover - core is always present on main
        return {"status": "skipped", "reason": f"core.normalize not importable: {e}"}
    if not hasattr(normalize, "suggest"):
        return {"status": "skipped", "reason": "core.normalize.suggest is not on this build (A's PR #17, D-040 part 1)"}
    cases = json.loads(TYPO_SET.read_text())["cases"]
    old = os.environ.get("GV_FUZZY")
    os.environ["GV_FUZZY"] = "1"
    try:
        rows = []
        for c in cases:
            out = normalize.suggest(c["typed"])
            s = out[0] if out else None
            choices = s["choices"] if s else []
            mode = s["mode"] if s else "none"
            meant_ing = _ingredients(normalize, c["meant"])
            silent_wrong = mode == "assumed" and bool(meant_ing) and _ingredients(normalize, s["assumed"]) != meant_ing
            rows.append({**c, "mode": mode, "choices": choices, "correct": c["meant"] in choices,
                         "silent_wrong": silent_wrong, "lookalike_assumed": c["lookalike"] and mode == "assumed"})
    finally:
        if old is None:
            os.environ.pop("GV_FUZZY", None)
        else:
            os.environ["GV_FUZZY"] = old
    return {"status": "ran", "set": "typos-v1", "n": len(rows),
            "correct": sum(r["correct"] for r in rows),
            "assumed": sum(r["mode"] == "assumed" for r in rows), "asked": sum(r["mode"] == "ask" for r in rows),
            "no_suggestion": sum(r["mode"] == "none" for r in rows),
            "silent_wrong": sum(r["silent_wrong"] for r in rows),
            "lookalike_assumed": sum(r["lookalike_assumed"] for r in rows),
            "rows": rows}


def _drug_frequency(universe) -> dict[str, float]:
    freq: dict[str, float] = defaultdict(float)
    for key, meta in universe.keys.items():
        for part in key.split("|"):
            freq[part.lower()] += float(meta.get("prior", 0) or 0)
    return {k: v for k, v in freq.items() if v > 0}


def tail_priors(buckets: list[list[str]], universe, unseen: str = "smallest") -> dict[str, float]:
    """`unseen` sets the frequency of a drug or lab missing from D's universe: "smallest" (the main reading) or
    "median" (a sensitivity check; it narrows the gap between common and rare drugs)."""
    freq = _drug_frequency(universe)
    vals = sorted(freq.values())
    floor = (vals[0] if unseen == "smallest" else vals[len(vals) // 2]) if vals else 1.0
    pr = {}
    for keys in buckets:
        for k in keys:
            a, _, b = k.partition("|")
            pr[k] = freq.get(a.lower(), floor) * freq.get(b.lower(), floor)
    return pr


def attack_partition(buckets: list[list[str]], priors: dict[str, float], n: int = 500, asks: int = 3, seed: int = 7) -> dict:
    """The core's two attackers on a fixed partition. Each patient asks about one real key, drawn from the priors, `asks`
    times; every ask sends that key's whole bucket. Repeat-ask attacker: intersect what was seen (always the same 8) and
    guess one at random. Statistical attacker: bet on the most common key in the bucket."""
    bucket_of = {k: i for i, keys in enumerate(buckets) for k in keys}
    keys = list(bucket_of)
    weights = [priors[k] for k in keys]
    rng = random.Random(seed)
    real = rng.choices(keys, weights=weights, k=n)
    hit_i = hit_s = 0
    for r in real:
        seen = [set(buckets[bucket_of[r]]) for _ in range(asks)]
        cand = sorted(set.intersection(*seen))
        hit_i += rng.choice(cand) == r
        hit_s += max(cand, key=lambda k: (priors[k], k)) == r
    total = sum(weights)
    ceiling = sum(max(priors[k] for k in b) for b in buckets) / total
    return {"n": n, "asks": asks, "repeat_ask": round(hit_i / n, 3), "statistical": round(hit_s / n, 3),
            "stat_attacker_ceiling": round(ceiling, 4), "uniform_floor": 0.125}


def run_tail(n: int = 500, seed: int = 7) -> dict:
    if not TAIL_FILE.exists():
        return {"status": "skipped", "reason": "data/buckets/tail-v1.json is not on this build (B's PR #15, D-040 part 2)"}
    raw = json.loads(TAIL_FILE.read_text())
    buckets = [list(b["keys"]) for b in raw["buckets"]]
    bad = [i for i, b in enumerate(buckets) if len(b) != 8]
    flat = [k for b in buckets for k in b]
    if bad or len(flat) != len(set(flat)):
        return {"status": "invalid", "reason": f"{len(bad)} buckets not of 8, {len(flat) - len(set(flat))} repeated keys (I5)"}
    u = load_universe()
    res = attack_partition(buckets, tail_priors(buckets, u), n=n, seed=seed)
    alt = attack_partition(buckets, tail_priors(buckets, u, unseen="median"), n=n, seed=seed)
    return {"status": "ran", "partition": raw.get("version", "tail-v1"), "buckets": len(buckets), "keys": len(flat),
            "priors": "synthetic: product of each drug's summed universe priors; unseen drugs and labs get the smallest",
            **res, "sensitivity_unseen_median": {k: alt[k] for k in ("repeat_ask", "statistical", "stat_attacker_ceiling")}}


def run(write: bool = True) -> dict:
    res = {"typos": run_typos(), "tail": run_tail()}
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "adaptive.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


if __name__ == "__main__":
    out = run()
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in out.items()}, indent=1))
