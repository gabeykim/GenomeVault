"""Fixed, versioned decoy buckets (I5, D-003, P6.5).

The partition lives in data/buckets/<version>.json and is never generated from a query.
Every member key of a bucket maps to the same bucket, so the bucket sent for a key
does not depend on which of its 8 members the user actually asked about.
"""
import json
import pathlib
from functools import lru_cache

from .contracts import Bucket

BUCKET_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "buckets"
CURRENT_VERSION = "v2"  # v1 stays frozen and loadable; v2 = frequency-balanced regroup + 16 keys


def kind_of(key: str) -> str:
    """Key family: gene_drug (`GENE:phenotype|drug`), drug_lab (`drug|lab<band>`), drug_drug (`a|b`)."""
    head = key.split("|", 1)[0]
    if ":" in head:
        return "gene_drug"
    parts = [p for p in key.split("|") if not p.startswith("dose")]
    if any(c in p for p in parts for c in "<>"):
        return "drug_lab"
    return "drug_drug"


@lru_cache(maxsize=None)
def load_buckets(version: str = CURRENT_VERSION) -> tuple[Bucket, ...]:
    raw = json.loads((BUCKET_DIR / f"{version}.json").read_text())
    if raw.get("version") != version:
        raise ValueError(f"bucket file version {raw.get('version')!r} != {version!r}")
    buckets = tuple(Bucket.model_validate(b) for b in raw["buckets"])
    seen: dict[str, str] = {}
    for b in buckets:
        if b.version != version:
            raise ValueError(f"bucket {b.id} has version {b.version!r}, expected {version!r}")
        for k in b.keys:
            if k in seen:
                raise ValueError(f"key {k!r} is in both {seen[k]} and {b.id} (I5: partition)")
            seen[k] = b.id
    return buckets


@lru_cache(maxsize=None)
def _index(version: str) -> dict[str, Bucket]:
    return {k: b for b in load_buckets(version) for k in b.keys}


def bucket_for(key: str, version: str = CURRENT_VERSION) -> Bucket | None:
    """The fixed bucket containing `key`, or None if the key is outside the universe
    (the router must then answer `no_data` rather than invent decoys, I4/I5)."""
    return _index(version).get(key)


def universe(version: str = CURRENT_VERSION) -> list[str]:
    return [k for b in load_buckets(version) for k in b.keys]
