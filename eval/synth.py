"""Synthetic patients for the red team (E1). All values are generated here, never real (I1).

Each patient belongs to one co-prescription scenario (a universe cluster), takes the drugs named in that
cluster's keys, and asks about 1..4 of the cluster's keys. The plan asks to vary the patient across trials so
the attacker can't just memorize Alex; Alex himself is available as `alex()` for the demo talking point.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from core.interfaces import load_profile
from eval.universe import LABS, Partition, Universe

GENES = {"CYP2C19": ["*1/*1", "*1/*2", "*2/*2", "*1/*17"], "CYP2D6": ["*1/*1", "*1/*4", "*4/*4", "*1/*2xN"],
         "CYP2C9": ["*1/*1", "*1/*2", "*1/*3"], "SLCO1B1": ["*1/*1", "*1/*5", "*5/*5"], "VKORC1": ["reference", "-1639G>A het"]}


@dataclass
class Patient:
    pid: str
    scenario: str
    topic_keys: list[str]                 # the real generalized keys this patient asks about (all inside the partition)
    meds: list[str]
    genotypes: dict[str, str]
    conditions: list[str]
    age: int
    labs: dict[str, float] = field(default_factory=dict)


def drugs_in(key: str) -> list[str]:
    return [p for p in key.split("|") if not p.isupper() and p not in LABS]


def scenario_weights(u: Universe, part: Partition, min_keys: int = 1) -> dict[str, float]:
    w = {}
    for s, ks in u.clusters.items():
        inside = [k for k in ks if part.bucket_for(k)]
        if len(inside) >= min_keys:
            w[s] = sum(u.prior(k) for k in inside)
    return w


def make_patient(i: int, rng: random.Random, u: Universe, part: Partition, n_keys: int | tuple[int, int] = 1,
                 min_scenario_keys: int = 1) -> Patient:
    weights = scenario_weights(u, part, min_scenario_keys)
    scenario = rng.choices(list(weights), weights=list(weights.values()))[0]
    pool = [k for k in u.clusters[scenario] if part.bucket_for(k)]
    lo, hi = (n_keys, n_keys) if isinstance(n_keys, int) else n_keys
    n = min(rng.randint(lo, hi), len(pool))
    keys, pool_w = [], {k: u.prior(k) for k in pool}
    while len(keys) < n:                          # prior-weighted sample without replacement
        k = rng.choices(list(pool_w), weights=list(pool_w.values()))[0]
        keys.append(k)
        pool_w.pop(k)
    meds = sorted({d for k in u.clusters[scenario] for d in drugs_in(k)})
    return Patient(pid=f"P{i:03d}", scenario=scenario, topic_keys=keys, meds=meds,
                   genotypes={g: rng.choice(v) for g, v in GENES.items()}, conditions=[scenario],
                   age=rng.randint(25, 85), labs={"egfr": rng.randint(30, 100), "potassium": round(rng.uniform(3.5, 5.6), 1)})


def make_patients(n: int, seed: int, u: Universe, part: Partition, n_keys=1, min_scenario_keys: int = 1) -> list[Patient]:
    rng = random.Random(seed)
    return [make_patient(i, rng, u, part, n_keys, min_scenario_keys) for i in range(n)]


def alex(topic_keys: list[str]) -> Patient:
    p = load_profile()
    labs = {}
    for l in sorted(p.labs, key=lambda l: l.date):
        labs[l.test.lower()] = l.value                    # latest wins
    return Patient(pid="ALEX", scenario="cardiac_post_stent", topic_keys=topic_keys, meds=[m.ingredient for m in p.meds],
                   genotypes=dict(p.genotypes), conditions=list(p.conditions), age=58, labs=labs)
