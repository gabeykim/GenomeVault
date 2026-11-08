"""One-off builder for data/buckets/v2.json (I5, D-003, D-006, P6.5).

Run once, offline, by a developer; never at runtime and never from a query. The output file is the
partition; this script only documents how it was chosen so a reviewer can re-check it:

    python data/buckets/build_v2.py <D's eval/fixtures/universe_v1.json> > data/buckets/v2.json

Goal (D-005 / message 20261108-1357-from-D): on v1 a statistical attacker who bets on a bucket's most
common key wins up to 31% (common key among rare ones). v2 groups keys of similar synthetic frequency
so top-prior / bucket-total is as close to 1/8 as possible, subject to:
  - one key family per bucket (gene_drug / drug_lab / drug_drug), sorted keys (existing tests);
  - at most 2 keys from one co-prescription cluster per bucket (D-006);
  - a drug never appears twice in a gene_drug or drug_lab bucket, at most twice in a drug_drug bucket;
  - at most 2 of Alex's drug pairs per bucket; omeprazole and pantoprazole pairs in different buckets (S6).
Priors are D's SYNTHETIC illustrative numbers (I1), not real prescribing data.
"""
import json
import random
import sys
from collections import Counter

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from core.decoys import kind_of, load_buckets  # noqa: E402

K = 8
SEED = 20261108
ITERS = 60000

# New keys for v2 (A's spelling: GENE:phenotype|drug, drug|lab<band>). Topic key in comment.
NEW_GENE = [
    "CYP2C19:poor_metabolizer|citalopram",      # Q05
    "CYP2C19:poor_metabolizer|sertraline",
    "CYP2C19:poor_metabolizer|omeprazole",
    "SLCO1B1:decreased_function|atorvastatin",
    "HLA-B:5801_positive|allopurinol",
    "HLA-B:1502_positive|carbamazepine",
    "CYP2D6:poor_metabolizer|tamoxifen",
    "CYP2C9:poor_metabolizer|phenytoin",
]
NEW_LAB = [
    "lisinopril|egfr<60",                       # Q12, Q20
    "simvastatin|alt>120",                      # Q14
    "apixaban|egfr<30",
    "acetaminophen|alt>120",
    "lithium|egfr<60",                          # no D prior yet -> DEFAULT_PRIOR, cluster bipolar
    "atorvastatin|alt>120",                     # no D prior yet -> diabetes_ckd
    "valproate|alt>120",                        # no D prior yet -> epilepsy
    "methotrexate|egfr<60",                     # no D prior yet -> rheumatoid
]
EXTRA_CLUSTERS = {
    "lithium|egfr": "bipolar",
    "atorvastatin|alt": "diabetes_ckd",
    "valproate|alt": "epilepsy",
    "methotrexate|egfr": "rheumatoid",
}
DEFAULT_PRIOR = 3
ALEX_MEDS = {"aspirin", "clopidogrel", "omeprazole", "simvastatin", "lisinopril", "ibuprofen", "pantoprazole"}


def topic(key: str) -> str:
    parts = [p for p in key.split("|") if not p.startswith("dose")]
    head = parts[0].split(":")[0]
    rest = [p.split("<")[0].split(">")[0] for p in parts[1:]]
    return "|".join([head, *rest])


def drugs(key: str) -> list[str]:
    fam = kind_of(key)
    parts = [p for p in key.split("|") if not p.startswith("dose")]
    if fam == "gene_drug":
        return [parts[1]]
    if fam == "drug_lab":
        return [parts[0]]
    return parts


def load_priors(priors_path: str, extra_clusters: dict[str, str]) -> tuple[dict[str, int], dict[str, set[str]]]:
    """D's synthetic topic priors and co-prescription clusters (topic -> cluster names)."""
    fx = json.loads(open(priors_path).read())
    prior = {k: v["prior"] for k, v in fx["keys"].items()}
    clusters: dict[str, set[str]] = {}
    for name, members in fx["clusters"].items():
        for t in members:
            clusters.setdefault(t, set()).add(name)
    for t, c in extra_clusters.items():
        if c:
            clusters.setdefault(t, set()).add(c)
    return prior, clusters


def main(priors_path: str) -> None:
    prior, clusters = load_priors(priors_path, EXTRA_CLUSTERS)
    keys = [k for b in load_buckets("v1") for k in b.keys] + NEW_GENE + NEW_LAB
    out, p = partition(keys, prior, clusters)
    emit("v2", out, p, (
        "Fixed partition (I5, D-003). Never regenerate from a query; a new partition is a new version "
        "file. v2 = v1's 96 keys + 16 new, regrouped by similar synthetic frequency with <= 2 keys per "
        "co-prescription cluster per bucket (D-006). Built once by data/buckets/build_v2.py from D's "
        "synthetic priors (eval/fixtures/universe_v1.json @ f88da85)."))


def partition(keys: list[str], prior: dict[str, int], clusters: dict[str, set[str]]) -> tuple[list[list[str]], dict]:
    """Frequency-balanced partition of `keys` into sorted buckets of K under the constraints above."""
    assert len(keys) == len(set(keys))
    p = {k: prior.get(topic(k), DEFAULT_PRIOR) for k in keys}

    def penalty(bucket: list[str]) -> int:
        fam = kind_of(bucket[0])
        bad = 0
        cc = Counter(c for k in bucket for c in clusters.get(topic(k), ()))
        bad += sum(n - 2 for n in cc.values() if n > 2)
        dc = Counter(d for k in bucket for d in drugs(k))
        cap = 2 if fam == "drug_drug" else 1
        bad += sum(n - cap for n in dc.values() if n > cap)
        if fam == "drug_drug":
            alex = [k for k in bucket if set(k.split("|")) <= ALEX_MEDS]
            bad += max(0, len(alex) - 2)
            bad += int("clopidogrel|omeprazole" in bucket and "clopidogrel|pantoprazole" in bucket)
        return bad

    def ratio(bucket: list[str]) -> float:
        return max(p[k] for k in bucket) / sum(p[k] for k in bucket)

    def score(buckets: list[list[str]]) -> tuple:
        return (sum(penalty(b) for b in buckets), max(ratio(b) for b in buckets),
                sum(ratio(b) ** 2 for b in buckets))

    rng = random.Random(SEED)
    out: list[list[str]] = []
    for fam in ("gene_drug", "drug_lab", "drug_drug"):
        fk = sorted((k for k in keys if kind_of(k) == fam), key=lambda k: (-p[k], k))
        n = len(fk) // K
        assert n * K == len(fk), (fam, len(fk))
        if n == 0:  # family not being rebuilt (build_v4 regroups only gene keys)
            continue
        # snake-draft start: spreads common keys across buckets
        buckets = [[] for _ in range(n)]
        for i, k in enumerate(fk):
            r, c = divmod(i, n)
            buckets[c if r % 2 == 0 else n - 1 - c].append(k)
        best = score(buckets)
        for _ in range(ITERS):
            a, b = rng.sample(range(n), 2)
            i, j = rng.randrange(K), rng.randrange(K)
            buckets[a][i], buckets[b][j] = buckets[b][j], buckets[a][i]
            s = score(buckets)
            if s <= best:
                best = s
            else:
                buckets[a][i], buckets[b][j] = buckets[b][j], buckets[a][i]
        assert best[0] == 0, (fam, best)
        print(f"{fam}: max attacker win {best[1]:.1%}", file=sys.stderr)
        out += [sorted(b) for b in buckets]

    order = {"gene_drug": 0, "drug_lab": 1, "drug_drug": 2}
    out.sort(key=lambda b: (order[kind_of(b[0])], b))
    return out, p


def emit(version: str, out: list[list[str]], p: dict, note: str) -> None:
    for i, b in enumerate(out, 1):
        r = max(p[k] for k in b) / sum(p[k] for k in b)
        print(f"b{i:02d} {r:.1%} " + " ".join(f"{topic(k)}({p[k]})" for k in b), file=sys.stderr)
    doc = {
        "version": version,
        "k": K,
        "note": note,
        "buckets": [{"id": f"b{i:02d}", "version": version, "keys": b} for i, b in enumerate(out, 1)],
    }
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
