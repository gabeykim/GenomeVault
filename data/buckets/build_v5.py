"""One-off builder for data/buckets/v5.json (I3, I5, D-003, D-006, D-021, P6.5).

Run once, offline, by a developer; never at runtime and never from a query:

    python data/buckets/build_v5.py <D's eval/fixtures/universe_v1.json> > data/buckets/v5.json

Why v5 (D's finding, message 20261108-1415-from-D-v3-results): v4 holds several exact variants of one
generalized topic (same gene + drug, other phenotype or dose band) in *different* buckets, e.g.
`CYP2C19:poor_metabolizer|clopidogrel` in b01 and `CYP2C19:intermediate_metabolizer|clopidogrel` in b02.
Their outbound text is the same, but which bucket leaves depends on the phenotype, so an observer who
guesses the topic also learns the genotype (I3). v5 keeps exactly one member per generalized topic and
lists the other variants as `aliases` of it: an alias maps to its member's bucket and gets the
member's answer (decoys.load_aliases, router._send_bucket). The member is the variant whose text asks
the most (a dosed key, whose text also covers the dose range), then the poor_* variant. The 4 freed gene
slots get 4 decoys on SNP-callable genes with distinct topics (no CYP2D6, D-021; no pantoprazole gene
key, S6). Only the gene buckets are regrouped (v2 method, D-006); the 13 lab and pair buckets are v4's
(= v3's), unchanged, because no lab or pair topic has variants. Priors are D's SYNTHETIC numbers (I1).
"""
import sys

from build_v2 import DEFAULT_PRIOR, emit, kind_of, load_priors, partition, topic  # (same directory)
from build_v3 import EXTRA_CLUSTERS

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from core.decoys import load_buckets  # noqa: E402

REPLACEMENTS = [
    "CYP2C9:poor_metabolizer|piroxicam",
    "DPYD:poor_metabolizer|capecitabine",
    "TPMT:poor_metabolizer|thioguanine",
    "UGT1A1:poor_metabolizer|atazanavir",
]


def _rank(key: str) -> tuple:
    """Order a variant group so its member comes first: dosed, then poor_*, then by spelling."""
    return (not any(p.startswith("dose") for p in key.split("|")), ":poor_" not in key, key)


def main(priors_path: str) -> None:
    prior, clusters = load_priors(priors_path, EXTRA_CLUSTERS)
    v4 = load_buckets("v4")
    groups: dict[str, list[str]] = {}
    for b in v4:
        for k in b.keys:
            groups.setdefault(topic(k), []).append(k)
    aliases: dict[str, str] = {}
    for ks in groups.values():
        if len(ks) > 1:
            assert all(kind_of(k) == "gene_drug" for k in ks), ks
            member, *others = sorted(ks, key=_rank)
            aliases.update({a: member for a in others})
    gene = [k for b in v4 if kind_of(b.keys[0]) == "gene_drug" for k in b.keys if k not in aliases]
    assert not {topic(k) for k in REPLACEMENTS} & {topic(k) for k in gene}
    assert len(gene) + len(REPLACEMENTS) == 32, len(gene)
    rest = [b.keys for b in v4 if kind_of(b.keys[0]) != "gene_drug"]
    out, p = partition(gene + REPLACEMENTS, prior, clusters)   # gene family only
    for b in rest:
        for k in b:
            p.setdefault(k, prior.get(topic(k), DEFAULT_PRIOR))
    emit("v5", out + rest, p, (
        "Fixed partition (I5, D-003). Never regenerate from a query; a new partition is a new version "
        "file. v5 = v4 with one member per generalized topic (I3): other phenotype / dose variants of a "
        "member are `aliases` that map to its bucket and share its answer, so the bucket that leaves never "
        "depends on the genotype. 4 freed gene slots hold decoys on SNP-callable genes; only the 4 gene "
        "buckets are regrouped (v2 method, D-006); the 13 lab and pair buckets are v4's, unchanged. Built "
        "once by data/buckets/build_v5.py from D's synthetic priors (eval/fixtures/universe_v1.json @ f69dc14)."),
        {"aliases": dict(sorted(aliases.items()))})


if __name__ == "__main__":
    main(sys.argv[1])
