"""Loaders shared by every evaluation (M11).

- Bucket partition: B's `data/buckets/v1.json` when it exists (real, G2+), otherwise D's stand-in
  `eval/fixtures/buckets_v1.json`. Results always record which one was used.
- Key universe with synthetic priors, domains and co-prescription clusters (eval/fixtures/universe_v1.json).
- The 20 scripted questions (eval/queries.json).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
from dataclasses import dataclass, field

from core.contracts import Bucket

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
REAL_BUCKETS = ROOT / "data" / "buckets" / "v1.json"
FIXTURE_BUCKETS = EVAL / "fixtures" / "buckets_v1.json"
UNIVERSE = EVAL / "fixtures" / "universe_v1.json"
QUERIES = EVAL / "queries.json"

_PHENO = re.compile(r"^([A-Z0-9-]+):[A-Za-z0-9_]+$")    # CYP2C19:poor_metabolizer, HLA-B:5701_positive
_LAB_THRESHOLD = re.compile(r"^([a-z_]+)[<>]=?[0-9.]+$")  # potassium>5.0
_DOSE = re.compile(r"^dose[<>]=?[0-9.]+mg$")             # dose>20mg
LABS = {"egfr", "potassium", "alt", "ast", "ck", "ldl", "inr", "sodium", "glucose", "tsh", "magnesium", "platelets"}


def generalize_key(local_key: str) -> str:
    """Strip everything personal from an exact local key, giving the outbound topic key.

    'CYP2C19:poor_metabolizer|clopidogrel'          -> 'CYP2C19|clopidogrel'
    'SLCO1B1:decreased_function|simvastatin|dose>20mg' -> 'SLCO1B1|simvastatin'
    'lisinopril|potassium>5.0'                        -> 'lisinopril|potassium'
    'clopidogrel|omeprazole'                          -> unchanged
    Eval-side model of P6.3; B's generalize.py is the source of truth once merged.
    """
    parts = []
    for p in local_key.split("|"):
        if _DOSE.match(p):
            continue
        m = _PHENO.match(p)
        if m:
            parts.append(m.group(1))
            continue
        m = _LAB_THRESHOLD.match(p.lower())
        parts.append(m.group(1) if m else p)
    gene = [p for p in parts if p.isupper()]          # CYP2C19, HLA-B (isupper ignores digits and '-')
    rest = [p.lower() for p in parts if p not in gene]
    labs = [p for p in rest if p in LABS]
    drugs = sorted(p for p in rest if p not in LABS)
    if drugs and labs:                                 # drug-lab key: drug first, then lab (mock X4 format)
        return "|".join(drugs + labs)
    return "|".join(gene + sorted(rest))


@dataclass
class Universe:
    keys: dict[str, dict]                    # key -> {"domain", "prior"}
    clusters: dict[str, list[str]]
    version: str

    def prior(self, key: str) -> float:
        return float(self.keys[key]["prior"])

    def domain(self, key: str) -> str:
        return self.keys[key]["domain"]

    def prior_dist(self) -> dict[str, float]:
        total = sum(v["prior"] for v in self.keys.values())
        return {k: v["prior"] / total for k, v in self.keys.items()}


@dataclass
class Partition:
    buckets: list[Bucket]
    source: str                              # "real:data/buckets/v1.json" or "fixture:eval/fixtures/buckets_v1.json"
    stats: dict = field(default_factory=dict)
    _index: dict[str, Bucket] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        for b in self.buckets:
            for k in b.keys:
                if k in self._index:
                    raise ValueError(f"key {k} is in two buckets ({self._index[k].id}, {b.id}); I5 needs a partition")
                self._index[k] = b

    @property
    def keys(self) -> list[str]:
        return list(self._index)

    def bucket_for(self, key: str) -> Bucket | None:
        """Fixed bucket of 8 for a generalized key; None means outside the universe (no-data path, I5)."""
        return self._index.get(key)

    @property
    def version(self) -> str:
        return self.buckets[0].version if self.buckets else "none"


def _parse_buckets(raw) -> list[Bucket]:
    if isinstance(raw, dict):
        version = raw.get("version", "v1")
        items = raw.get("buckets", [])
    else:
        version, items = "v1", raw
    out = []
    for i, b in enumerate(items):
        if isinstance(b, dict):
            out.append(Bucket(id=b.get("id") or b.get("bucket_id") or f"B{i:02d}",
                              version=b.get("version", version),
                              keys=b.get("keys") or b.get("topics")))
        else:
            out.append(Bucket(id=f"B{i:02d}", version=version, keys=list(b)))
    return out


MIN_OVERLAP = 0.25        # share of the real partition's keys that need synthetic priors before evals switch to it


def generalized_view(buckets: list[Bucket]) -> tuple[list[Bucket], dict]:
    """B's partition is keyed by exact local keys (phenotype, lab threshold, dose). Evals measure the topic an
    attacker can recover, so they work on the generalized key of each member. Keys that would collide after
    generalizing keep their original spelling. Returns the view and stats about personal detail in the raw keys."""
    gen = [[generalize_key(k) for k in b.keys] for b in buckets]
    counts: dict[str, int] = {}
    for g in gen:
        for k in g:
            counts[k] = counts.get(k, 0) + 1
    out = [Bucket(id=b.id, version=b.version, keys=[gk if counts[gk] == 1 else k for k, gk in zip(b.keys, g)])
           for b, g in zip(buckets, gen)]
    raw = [k for b in buckets for k in b.keys]
    stats = {"raw_keys": len(raw),
             "raw_keys_with_phenotype": sum(bool(_PHENO.match(p)) for k in raw for p in k.split("|")),
             "raw_keys_with_threshold_or_dose": sum(any(_LAB_THRESHOLD.match(p.lower()) or _DOSE.match(p) for p in k.split("|")) for k in raw),
             "collisions_kept_raw": sum(1 for c in counts.values() if c > 1)}
    return out, stats


def load_partition(prefer_real: bool = True, path: pathlib.Path | None = None) -> Partition:
    """B's real partition when it exists and overlaps D's universe enough; otherwise D's stand-in (and say why)."""
    src = path or (pathlib.Path(os.environ["EVAL_BUCKETS"]) if os.environ.get("EVAL_BUCKETS") else REAL_BUCKETS)
    if prefer_real and src.exists():
        view, stats = generalized_view(_parse_buckets(json.loads(src.read_text())))
        part = Partition(view, f"real:{src.relative_to(ROOT) if src.is_relative_to(ROOT) else src.name}")
        part.stats = stats
        u = load_universe()
        overlap = sum(part.bucket_for(k) is not None for k in u.keys) / len(u.keys)
        part.stats["universe_overlap"] = round(overlap, 3)
        part.stats["partition_keys_without_prior"] = sum(k not in u.keys for k in part.keys)
        covered = sum(k in u.keys for k in part.keys) / len(part.keys)
        if covered >= MIN_OVERLAP:
            return part
        fb = load_partition(prefer_real=False)
        fb.stats = {"fallback_reason": f"only {covered:.0%} of the real partition's keys have synthetic priors", **stats}
        return fb
    part = Partition(_parse_buckets(json.loads(FIXTURE_BUCKETS.read_text())), "fixture:eval/fixtures/buckets_v1.json")
    part.stats = {}
    return part


def load_universe() -> Universe:
    raw = json.loads(UNIVERSE.read_text())
    return Universe(keys=raw["keys"], clusters=raw["clusters"], version=raw["version"])


def load_queries() -> list[dict]:
    return json.loads(QUERIES.read_text())["queries"]


def priors_for(partition: Partition, universe: Universe) -> dict[str, float]:
    """Synthetic priors over the partition's keys; keys missing from the universe file get the median prior."""
    known = [universe.prior(k) for k in partition.keys if k in universe.keys]
    median = sorted(known)[len(known) // 2] if known else 1.0
    return {k: (universe.prior(k) if k in universe.keys else median) for k in partition.keys}


def domain_for(key: str, universe: Universe) -> str:
    return universe.keys.get(key, {}).get("domain", "unknown")
