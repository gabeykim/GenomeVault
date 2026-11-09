"""Red team for B's I7 wording filter (B-013): adversarial cloud-answer texts that should be rejected, and
neutral ones that should pass. Scores `core.validator.wording_problems` when B's validator is importable;
otherwise reports `skipped`. A miss is serious (an answer that breaks I7 would become a Fact); a false alarm is
cheap (the key reads `no_data`, which is always allowed). Run: python -m eval.wording"""
from __future__ import annotations

import importlib
import json
from collections import defaultdict

from eval.universe import EVAL, ROOT

CASES = EVAL / "fixtures" / "wording_cases.json"
RESULTS = ROOT / "eval" / "results"


def load_cases() -> list[dict]:
    return json.loads(CASES.read_text())["cases"]


def run(write: bool = True) -> dict:
    cases = load_cases()
    try:
        validator = importlib.import_module("core.validator")
        problems = validator.wording_problems
    except (ImportError, AttributeError):
        res = {"status": "skipped: core.validator.wording_problems not in this build (B-013, PR #2)", "n": len(cases)}
        if write:
            RESULTS.mkdir(parents=True, exist_ok=True)
            (RESULTS / "wording.json").write_text(json.dumps(res, indent=1) + "\n")
        return res
    rows, fam = [], defaultdict(lambda: [0, 0])
    for c in cases:
        found = problems(c["text"])
        rejected = bool(found)
        ok = rejected == (c["expect"] == "reject")
        rows.append({"id": c["id"], "family": c["family"], "expect": c["expect"], "rejected": rejected, "ok": ok, "reasons": found})
        if c["expect"] == "reject":
            fam[c["family"]][0] += rejected
            fam[c["family"]][1] += 1
    rej = [r for r in rows if r["expect"] == "reject"]
    acc = [r for r in rows if r["expect"] == "accept" and r["family"] != "by_design"]
    res = {"status": "ran", "n": len(cases),
           "caught": sum(r["rejected"] for r in rej), "should_reject": len(rej),
           "false_alarms": sum(r["rejected"] for r in acc), "should_accept": len(acc),
           "by_design_rejected": sum(r["rejected"] for r in rows if r["family"] == "by_design"),
           "by_family": {k: {"caught": v[0], "of": v[1]} for k, v in fam.items()},
           "misses": [{"id": r["id"], "family": r["family"], "text": next(c["text"] for c in cases if c["id"] == r["id"])}
                      for r in rej if not r["rejected"]],
           "false_alarm_cases": [{"id": r["id"], "reasons": r["reasons"]} for r in acc if r["rejected"]],
           "rows": rows}
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "wording.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    return res


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in run().items() if k != "rows"}, indent=1, ensure_ascii=False))
