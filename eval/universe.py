"""Loaders shared by every evaluation (M11).

- Bucket partition: B's `data/buckets/v1.json` when it exists (real, G2+), otherwise D's stand-in
  `eval/fixtures/buckets_v1.json`. Results always record which one was used.
- Key universe with synthetic priors, domains and co-prescription clusters (eval/fixtures/universe_v1.json).
- The 20 scripted questions (eval/queries.json).
"""
from __future__ import annotations

import json
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

_PHENO = re.compile(r"^([A-Z0-9-]+):[a-z_]+$")          # CYP2C19:poor_metabolizer
_LAB_THRESHOLD = re.compile(r"^([a-z_]+)[<>]=?[0-9.]+$")  # potassium>5.0
_DOSE = re.compile(r"^dose[<>]=?[0-9.]+mg$")             # dose>20mg
LABS = {"egfr", "potassium", "alt", "ck", "ldl", "inr", "sodium"}


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


def load_partition(prefer_real: bool = True) -> Partition:
    if prefer_real and REAL_BUCKETS.exists():
        return Partition(_parse_buckets(json.loads(REAL_BUCKETS.read_text())), "real:data/buckets/v1.json")
    return Partition(_parse_buckets(json.loads(FIXTURE_BUCKETS.read_text())), "fixture:eval/fixtures/buckets_v1.json")


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
