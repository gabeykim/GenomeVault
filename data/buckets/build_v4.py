"""One-off builder for data/buckets/v4.json (I5, D-003, D-006, D-021, P6.5).

Run once, offline, by a developer; never at runtime and never from a query:

    python data/buckets/build_v4.py <D's eval/fixtures/universe_v1.json> > data/buckets/v4.json

Why v4: D-021 / PLAN v1.2 P5 makes CYP2D6 `not_assessed` for every user (gene deletions and
duplications cannot be called from SNP data; no rule may use it). The app's code is public, so an
observer knows a CYP2D6 key can never be a real query, and every CYP2D6 member of a bucket is a
known decoy. v3 had 7 of them in the 4 gene buckets, which cut the effective k to 4 in b04 and to
6-7 in b01-b03. That breaks I5 (k = 8). v4 swaps the 7 CYP2D6 keys for 7 keys on SNP-callable genes
and rebuilds only the gene buckets with v2's method. The 13 lab and pair buckets are copied
unchanged from v3, so their ids and members stay the same. Priors are D's SYNTHETIC numbers (I1).
"""
import sys

from build_v2 import DEFAULT_PRIOR, emit, kind_of, load_priors, partition, topic  # (same directory)
from build_v3 import EXTRA_CLUSTERS

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from core.decoys import load_buckets  # noqa: E402

NOT_ASSESSED_GENES = ("CYP2D6",)   # PLAN P5 / D-021: never a real query, so never a decoy either

# Replacement decoys: SNP-callable genes with real CPIC/DPWG topics. No pantoprazole gene key, so the
# omeprazole send cannot pre-fill a pantoprazole gene answer (S6 no-extrapolation beat).
REPLACEMENTS = [
    "CYP2C19:poor_metabolizer|amitriptyline",
    "CYP2C19:poor_metabolizer|escitalopram",
    "CYP2C19:poor_metabolizer|voriconazole",
    "CYP2C9:poor_metabolizer|meloxicam",
    "HLA-A:3101_positive|carbamazepine",
    "SLCO1B1:poor_function|atorvastatin",
    "TPMT:poor_metabolizer|mercaptopurine",
]


def main(priors_path: str) -> None:
    prior, clusters = load_priors(priors_path, EXTRA_CLUSTERS)
    v3 = load_buckets("v3")
    gene = [k for b in v3 if kind_of(b.keys[0]) == "gene_drug" for k in b.keys
            if k.split(":")[0] not in NOT_ASSESSED_GENES]
    assert len(gene) + len(REPLACEMENTS) == 32
    rest = [b.keys for b in v3 if kind_of(b.keys[0]) != "gene_drug"]
    out, p = partition(gene + REPLACEMENTS, prior, clusters)   # gene family only
    for b in rest:
        for k in b:
            p.setdefault(k, prior.get(topic(k), DEFAULT_PRIOR))
    emit("v4", out + rest, p, (
        "Fixed partition (I5, D-003). Never regenerate from a query; a new partition is a new version "
        "file. v4 = v3 with the 7 CYP2D6 decoys (not_assessed for every user, D-021, so known decoys) "
        "swapped for 7 keys on SNP-callable genes; only the 4 gene buckets are regrouped (v2 method, "
        "D-006); the 13 lab and pair buckets are v3's, unchanged. Built once by "
        "data/buckets/build_v4.py from D's synthetic priors (eval/fixtures/universe_v1.json @ f69dc14)."))


if __name__ == "__main__":
    main(sys.argv[1])
