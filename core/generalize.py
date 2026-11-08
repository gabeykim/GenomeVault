"""Generalize flags / exact keys into outbound-safe Topics (P6.3, P6.4, I3).

One Topic per concept (one exact key). The Topic text is phrased for *all* phenotypes
of a gene and *all* bands of a lab, and never carries a number, a dose, a genotype,
a date or any other field from the profile. Thresholds inside a key (e.g. `dose>20mg`,
`potassium>5.0`) are dropped too: the text asks about the whole range.

`Topic.key` stays the exact key so the answer can be stored in the KB under it (I4);
only `Topic.text` is meant to leave the device, and validator.py checks it before send.
"""
import re

from .contracts import Flag, Topic
from .decoys import kind_of

# Phenotype families: the suffix of the phenotype token picks the full list to ask about.
_PHENOTYPE_FAMILIES: list[tuple[str, str]] = [
    ("metabolizer", "every metabolizer phenotype (poor, intermediate, normal, rapid, ultrarapid)"),
    ("function", "every transporter function level (poor, decreased, normal, increased)"),
    ("sensitivity", "every sensitivity level (low, normal, high)"),
    ("positive", "carrier status (carrier or non-carrier)"),
    ("negative", "carrier status (carrier or non-carrier)"),
    ("deficient", "every enzyme activity level (deficient, intermediate, normal)"),
]
_ANY_PHENOTYPE = "every known phenotype"

_LAB_NAMES = {
    "egfr": "kidney function (eGFR)",
    "potassium": "serum potassium",
    "sodium": "serum sodium",
    "magnesium": "serum magnesium",
    "glucose": "blood glucose",
    "tsh": "thyroid function (TSH)",
    "alt": "liver enzymes (ALT)",
    "ck": "creatine kinase (CK)",
    "inr": "INR",
}

_LAB_RE = re.compile(r"^([a-z0-9]+)\s*[<>]=?\s*[0-9.]+$")
_DRUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _phenotype_phrase(phenotype: str) -> str:
    for suffix, phrase in _PHENOTYPE_FAMILIES:
        if phenotype.endswith(suffix):
            return phrase
    return _ANY_PHENOTYPE


def _drug(token: str) -> str:
    if not _DRUG_RE.match(token):
        raise ValueError(f"not a drug ingredient token: {token!r}")
    return token


def _parts(key: str) -> tuple[list[str], bool]:
    """Split a key into its non-dose parts; report whether a dose condition was present."""
    parts = [p.strip() for p in key.lower().split("|") if p.strip()]
    dosed = any(p.startswith("dose") for p in parts)
    return [p for p in parts if not p.startswith("dose")], dosed


def topic_for_key(key: str) -> Topic:
    """The single generalized Topic for one exact key."""
    parts, dosed = _parts(key)
    dose_clause = ", and how the answer changes across the dose range" if dosed else ""
    kind = kind_of(key)

    if kind == "gene_drug":
        if len(parts) != 2 or ":" not in parts[0]:
            raise ValueError(f"malformed gene-drug key: {key!r}")
        phenotype = parts[0].split(":", 1)[1]
        gene = key.split("|", 1)[0].split(":", 1)[0].strip()  # keep the gene symbol's case
        drug = _drug(parts[1])
        text = (f"For {drug}, what do pharmacogenomic guidelines say about {gene}, "
                f"covering {_phenotype_phrase(phenotype)}{dose_clause}?")
    elif kind == "drug_lab":
        if len(parts) != 2:
            raise ValueError(f"malformed drug-lab key: {key!r}")
        drug_tok, lab_tok = parts
        if not _LAB_RE.match(lab_tok):
            drug_tok, lab_tok = lab_tok, drug_tok
        m = _LAB_RE.match(lab_tok)
        if not m:
            raise ValueError(f"malformed drug-lab key: {key!r}")
        lab = _LAB_NAMES.get(m.group(1), m.group(1).upper())
        text = (f"How should {_drug(drug_tok)} use be monitored or adjusted across "
                f"every range of {lab} (low, normal and high){dose_clause}?")
    else:
        if len(parts) != 2:
            raise ValueError(f"drug-drug key must name exactly two drugs: {key!r}")
        a, b = sorted(_drug(p) for p in parts)
        text = (f"Is an interaction between {a} and {b} listed, and if so what is its "
                f"mechanism and clinical significance{dose_clause}?")
    return Topic(key=key, text=text)


def generalize(flag: Flag) -> list[Topic]:
    """Flag -> outbound-safe Topics, one concept each (P6.3/P6.4).

    Allergy flags never go to the cloud (the allergy list is a personal field), so they
    generalize to nothing and the router answers them locally."""
    if flag.engine == "allergy":
        return []
    return [topic_for_key(flag.key)]
