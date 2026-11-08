"""One-off builder for data/buckets/v3.json (I5, D-003, D-006, P6.5).

Run once, offline, by a developer; never at runtime and never from a query:

    python data/buckets/build_v3.py <D's eval/fixtures/universe_v1.json> > data/buckets/v3.json

Why v3: A's real rule tables (PR #1, A-003) can emit 15 exact keys that are not in v2, among them
`CYP2C19:intermediate_metabolizer|clopidogrel` (needs_cloud) and the NSAID class expansions that D's
Q17 marks `in_universe`. A key outside the universe can never be sent (I4/I5 no_data), so v3 = v2's
112 keys + those 15 + 9 decoy keys that fill the gene and pair families to multiples of 8 (136 keys,
17 buckets: 4 gene, 3 lab, 10 pair). Same method and constraints as v2 (see build_v2.py). Priors are D's SYNTHETIC numbers (I1).
"""
import sys

from build_v2 import DEFAULT_PRIOR, emit, load_priors, partition  # noqa: F401  (same directory)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from core.decoys import load_buckets  # noqa: E402

# Keys A's rule tables produce that v2 lacks (A-003, message 20261108-1359-from-A).
FROM_A_GENE = [
    "CYP2C19:intermediate_metabolizer|clopidogrel",
    "SLCO1B1:poor_function|simvastatin",
]
FROM_A_PAIR = [
    "aspirin|celecoxib", "aspirin|naproxen", "celecoxib|clopidogrel", "celecoxib|lisinopril",
    "celecoxib|prasugrel", "celecoxib|ticagrelor", "clopidogrel|esomeprazole", "clopidogrel|naproxen",
    "ibuprofen|prasugrel", "ibuprofen|ticagrelor", "lisinopril|naproxen", "naproxen|prasugrel",
    "naproxen|ticagrelor",
]
# Decoy keys: well-known pharmacogenomic / interaction topics with a D prior, distinct topics where possible.
FILL_GENE = [
    "CYP2D6:poor_metabolizer|metoprolol",
    "CYP2D6:poor_metabolizer|paroxetine",
    "CYP2D6:ultrarapid_metabolizer|ondansetron",
    "CYP2C9:poor_metabolizer|celecoxib",
    "CYP2C9:poor_metabolizer|ibuprofen",
    "SLCO1B1:poor_function|rosuvastatin",
]
FILL_PAIR = ["celecoxib|warfarin", "ibuprofen|warfarin", "naproxen|warfarin"]

# Clusters for topics D's fixture doesn't list. Newer P2Y12 + NSAID pairs get their own cluster so the
# cardiac_post_stent cap (<= 2 per bucket) stays satisfiable.
EXTRA_CLUSTERS = {
    "lithium|egfr": "bipolar",
    "atorvastatin|alt": "diabetes_ckd",
    "valproate|alt": "epilepsy",
    "methotrexate|egfr": "rheumatoid",
    "aspirin|celecoxib": "chronic_pain",
    "aspirin|naproxen": "chronic_pain",
    "celecoxib|lisinopril": "chronic_pain",
    "lisinopril|naproxen": "chronic_pain",
    "celecoxib|clopidogrel": "cardiac_post_stent",
    "clopidogrel|naproxen": "chronic_pain",
    "celecoxib|prasugrel": "acs_nsaid",
    "celecoxib|ticagrelor": "acs_nsaid",
    "ibuprofen|prasugrel": "acs_nsaid",
    "ibuprofen|ticagrelor": "acs_nsaid",
    "naproxen|prasugrel": "acs_nsaid",
    "naproxen|ticagrelor": "acs_nsaid",
    "celecoxib|warfarin": "anticoagulation",
    "ibuprofen|warfarin": "anticoagulation",
    "naproxen|warfarin": "anticoagulation",
}


def main(priors_path: str) -> None:
    prior, clusters = load_priors(priors_path, EXTRA_CLUSTERS)
    keys = [k for b in load_buckets("v2") for k in b.keys] + FROM_A_GENE + FROM_A_PAIR + FILL_GENE + FILL_PAIR
    out, p = partition(keys, prior, clusters)
    emit("v3", out, p, (
        "Fixed partition (I5, D-003). Never regenerate from a query; a new partition is a new version "
        "file. v3 = v2's 112 keys + the 15 keys A's rule tables can emit (A-003) + 9 decoy keys, "
        "regrouped by similar synthetic frequency with <= 2 keys per co-prescription cluster per bucket "
        "(D-006). Built once by data/buckets/build_v3.py from D's synthetic priors "
        "(eval/fixtures/universe_v1.json @ eddea32)."))


if __name__ == "__main__":
    main(sys.argv[1])
