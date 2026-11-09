"""One-off builder for data/buckets/tail-v1.json (D-040 part 2, I3, I5, P6.5).

Run once, offline, by a developer; never at runtime and never from a query:

    python data/buckets/build_tail_v1.py > data/buckets/tail-v1.json

The long-tail partition (flag GV_TAIL) covers what the core partition (v5) does not:
  - every drug-drug pair over A's ingredient vocabulary (data/rules/drug_names.json, plus the core
    universe's drugs), and
  - one drug-lab key per ingredient and lab (`drug|<lab><band>`), with one fixed band per lab. The
    topic text asks about every range of the lab (generalize.topic_for_key), so other bands of the same
    drug + lab are the same topic; the router maps them onto this one key (never a second bucket, I3).
Keys already in v5 (members or aliases) are left out: core first. Ingredient tokens that topic_for_key
cannot phrase (underscores or spaces, e.g. st_johns_wort, potassium chloride) are left out too.

No synthetic priors exist for these keys, so there is no frequency tier to group by: each family is
shuffled with a fixed seed and cut into buckets of 8 (one family per bucket). The leftover keys of the
two families share one mixed bucket, padded with `drug|ldl>190` keys (a lab no other tail key uses).
Same file for every user; a new tail partition is a new version file (I5).
"""
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.contracts import pair_key  # noqa: E402
from core.decoys import load_aliases, load_buckets  # noqa: E402
from core.generalize import topic_for_key  # noqa: E402
from core.validator import _key_drugs  # noqa: E402

VERSION = "tail-v1"
K = 8
SEED = 20261108
BANDS = {   # one fixed band per lab; the text covers every range (I3)
    "egfr": "egfr<60", "potassium": "potassium>5.0", "sodium": "sodium<135", "magnesium": "magnesium<1.8",
    "glucose": "glucose>180", "tsh": "tsh>4.5", "alt": "alt>120", "ck": "ck>1000", "inr": "inr>3.0",
}
PAD_BAND = "ldl>190"
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")


def ingredients() -> list[str]:
    names = json.loads((ROOT / "data" / "rules" / "drug_names.json").read_text())["names"]
    out = {i.strip().lower() for ings in names.values() for i in ings}
    for b in load_buckets():
        for k in b.keys:
            out |= _key_drugs(k)
    return sorted(d for d in out if _TOKEN.match(d))


def build() -> dict:
    core = {k for b in load_buckets() for k in b.keys} | set(load_aliases())
    core_lab = {(d, k.split("|")[-1].split("<")[0].split(">")[0]) for k in core for d in _key_drugs(k)
                if any(c in k for c in "<>") and ":" not in k}
    drugs = ingredients()
    dd = [pair_key(a, b) for i, a in enumerate(drugs) for b in drugs[i + 1:]]
    dd = [k for k in dd if k not in core]
    dl = [f"{d}|{band}" for d in drugs for lab, band in BANDS.items() if (d, lab) not in core_lab]
    rng = random.Random(SEED)
    rng.shuffle(dd)
    rng.shuffle(dl)
    groups: list[list[str]] = []
    rest: list[str] = []
    for fam in (dd, dl):
        n = len(fam) - len(fam) % K
        groups += [fam[i:i + K] for i in range(0, n, K)]
        rest += fam[n:]
    pads = iter(f"{d}|{PAD_BAND}" for d in drugs)
    while len(rest) % K:
        rest.append(next(pads))
    groups += [rest[i:i + K] for i in range(0, len(rest), K)]
    for g in groups:
        for k in g:
            topic_for_key(k)   # every key must be phrasable (raises otherwise)
    buckets = [{"id": f"tail-{i + 1:04d}", "version": VERSION, "keys": sorted(g)} for i, g in enumerate(groups)]
    return {
        "version": VERSION,
        "note": ("Long-tail fixed partition (D-040 part 2, flag GV_TAIL; I5). Every drug-drug pair over A's "
                 "ingredient vocabulary and one drug-lab key per ingredient and lab, minus v5's keys. Seeded "
                 "shuffle per family, k = 8, no priors (no frequency tier). Never regenerate from a query; "
                 "built once by data/buckets/build_tail_v1.py."),
        "buckets": buckets,
    }


if __name__ == "__main__":
    json.dump(build(), sys.stdout, indent=1)
    sys.stdout.write("\n")
