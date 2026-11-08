"""Fixed, versioned decoy buckets (I5, D-003, P6.5).

The partition lives in data/buckets/<version>.json and is never generated from a query.
Every member key of a bucket maps to the same bucket, so the bucket sent for a key
does not depend on which of its 8 members the user actually asked about.

From v5 a partition file may also list `aliases`: exact variant keys of a member's generalized topic
(another phenotype or dose band of the same gene + drug). The outbound text is the same for every
variant (generalize.py asks about all phenotypes), so a variant is not a separate member: it maps to
its canonical member's bucket, and the member's answer is stored under the variant's key too. Without
this, two variants of one topic in different buckets would let the bucket that leaves reveal the
genotype (I3; D's finding on v3).
"""
import json
import pathlib
from functools import lru_cache

from .contracts import Bucket

BUCKET_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "buckets"
CURRENT_VERSION = "v5"  # v1-v4 stay frozen and loadable; v5 = one bucket per generalized topic (aliases, I3)


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
def load_aliases(version: str = CURRENT_VERSION) -> dict[str, str]:
    """Variant key -> canonical member key (empty before v5). Every target is a member; no alias is."""
    raw = json.loads((BUCKET_DIR / f"{version}.json").read_text())
    aliases = dict(raw.get("aliases", {}))
    members = {k for b in load_buckets(version) for k in b.keys}
    for a, c in aliases.items():
        if a in members or c not in members:
            raise ValueError(f"alias {a!r} -> {c!r}: an alias must not be a member and must point at one (I5)")
    return aliases


def canonical(key: str, version: str = CURRENT_VERSION) -> str:
    """The member key whose outbound text answers `key` (itself unless it is an alias)."""
    return load_aliases(version).get(key, key)


def aliases_of(key: str, version: str = CURRENT_VERSION) -> list[str]:
    """Variant keys whose answer is the member `key`'s answer."""
    return sorted(a for a, c in load_aliases(version).items() if c == key)


@lru_cache(maxsize=None)
def _index(version: str) -> dict[str, Bucket]:
    return {k: b for b in load_buckets(version) for k in b.keys}


def bucket_for(key: str, version: str = CURRENT_VERSION) -> Bucket | None:
    """The fixed bucket containing `key` (or its canonical member, for an alias), or None if the key is
    outside the universe (the router must then answer `no_data` rather than invent decoys, I4/I5)."""
    return _index(version).get(canonical(key, version))


def universe(version: str = CURRENT_VERSION) -> list[str]:
    """Member keys (the keys whose texts are sent). Aliases are not members; see `load_aliases`."""
    return [k for b in load_buckets(version) for k in b.keys]
