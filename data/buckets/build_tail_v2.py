"""One-off builder for data/buckets/tail-v2.json (D-040 part 2 "grouped by frequency tier where priors
exist", I3, I5, P6.5). Same keys as tail-v1; only the grouping changes.

Run once, offline, by a developer; never at runtime and never from a query:

    python data/buckets/build_tail_v2.py <D's eval/fixtures/universe_v1.json> > data/buckets/tail-v2.json

Why a v2: tail-v1 was a seeded shuffle with no frequency balancing, so a bucket often held one pair with a
common drug among seven rare ones and D's statistical attacker (E1) won 51-59% of the time (D-017).

Tail keys have no priors of their own. Each part of a key (drug, or lab band) gets a synthetic frequency: the
sum of its priors in D's universe file (same reading as eval/adaptive.py). Keys are tiered by
  1. how many of their parts are unseen in the universe (0, 1 or 2), then
  2. the product of the seen parts' frequencies, most common first,
and each family (drug-drug, drug-lab) is cut into consecutive buckets of 8. Tiering by the unseen count first
keeps every bucket's keys in one unseen class, so the order inside a bucket does not depend on what value an
attacker assigns to unseen drugs. Ties are broken by a seeded shuffle. Leftovers of the two families share
the last mixed bucket(s). Same file for every user; a new tail partition is a new version file (I5).
"""
import json
import math
import pathlib
import random
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from build_tail_v1 import K, SEED  # noqa: E402  (same directory)
from build_tail_v1 import build as build_v1  # noqa: E402
from core.generalize import topic_for_key  # noqa: E402

VERSION = "tail-v2"
DEFAULT_UNIVERSE = ROOT / "eval" / "fixtures" / "universe_v1.json"
UNIVERSE_PIN = "eval/fixtures/universe_v1.json"


def part_frequency(universe_path) -> dict[str, float]:
    keys = json.loads(pathlib.Path(universe_path).read_text())["keys"]
    freq: dict[str, float] = defaultdict(float)
    for key, meta in keys.items():
        for part in key.split("|"):
            freq[part.lower()] += float(meta.get("prior", 0) or 0)
    return {k: v for k, v in freq.items() if v > 0}


def tier(key: str, freq: dict[str, float]) -> tuple[int, float]:
    parts = [p.lower() for p in key.split("|")]
    seen = [freq[p] for p in parts if p in freq]
    return len(parts) - len(seen), -math.prod(seen)


def build(universe_path=DEFAULT_UNIVERSE) -> dict:
    freq = part_frequency(universe_path)
    keys = [k for b in build_v1()["buckets"] for k in b["keys"]]
    dd = sorted(k for k in keys if not any(c in k for c in "<>"))
    dl = sorted(k for k in keys if any(c in k for c in "<>"))
    rng = random.Random(SEED)
    groups: list[list[str]] = []
    rest: list[str] = []
    for fam in (dd, dl):
        rng.shuffle(fam)                                  # tie-break only
        fam.sort(key=lambda k: tier(k, freq))             # stable: shuffled order kept inside a tier
        n = len(fam) - len(fam) % K
        groups += [fam[i:i + K] for i in range(0, n, K)]
        rest += fam[n:]
    assert len(rest) % K == 0, "tail-v1 key count is a multiple of 8"
    rest.sort(key=lambda k: tier(k, freq))
    groups += [rest[i:i + K] for i in range(0, len(rest), K)]
    for g in groups:
        for k in g:
            topic_for_key(k)
    buckets = [{"id": f"tail-{i + 1:04d}", "version": VERSION, "keys": sorted(g)} for i, g in enumerate(groups)]
    return {
        "version": VERSION,
        "note": ("Long-tail fixed partition (D-040 part 2, flag GV_TAIL; I5). Same keys as tail-v1, grouped by "
                 "frequency tier: unseen-part count, then the product of each part's summed synthetic priors from "
                 f"D's {UNIVERSE_PIN}; k = 8, one family per bucket. Never regenerate from a query; built once "
                 "by data/buckets/build_tail_v2.py."),
        "buckets": buckets,
    }


if __name__ == "__main__":
    json.dump(build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_UNIVERSE), sys.stdout, indent=1)
    sys.stdout.write("\n")
