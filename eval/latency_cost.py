"""E3 latency, cloud usage and answer coverage (PLAN P7): local-only vs cloud-only vs hybrid on the 20 questions.

Simulated: counts follow from the design; latency/tokens use MODELLED constants (eval/backends.py).
Quality 1-5 against the reference answers needs a judge model (eval/llm_client.py) on the live build; until then
the table reports coverage: the share of questions reaching the best answer state queries.json expects. Hybrid loses
coverage when a needed key is outside the partition (I5), which is a real cost of the design and reported as such.
Run: python -m eval.latency_cost"""
from __future__ import annotations

import json
import os
import statistics
import time

from eval.backends import LiveBackend, SimBackend
from eval.charts import grouped_bars, stacked_panels
from eval.universe import ROOT, load_partition, load_queries

RESULTS, CHARTS = ROOT / "eval" / "results", ROOT / "docs" / "charts"
MODES = ["local_only", "cloud_only", "hybrid"]
LABELS = {"local_only": "Local only", "cloud_only": "Cloud only\n(naive)", "hybrid": "Hybrid\n(GenomeVault)"}


DEFAULT_DELAY = "0.3,2.0"      # B-009 live default for GV_DELAY_S


def run_live(delays: str) -> dict:
    """Hybrid on the integrated build with GV_DELAY_S=delays; cold KB; cover traffic off (B-009)."""
    qs = load_queries()
    old = os.environ.get("GV_DELAY_S")
    os.environ["GV_DELAY_S"] = delays
    try:
        be = LiveBackend()
        be.reset()
        t0 = time.perf_counter()
        rs = [be.ask(q) for q in qs]
        wall = time.perf_counter() - t0
    finally:
        if old is None:
            os.environ.pop("GV_DELAY_S", None)
        else:
            os.environ["GV_DELAY_S"] = old
    sent = [r for r in rs if r.cloud_calls]
    return {"backend": be.name, "GV_DELAY_S": delays, "median_latency_ms": round(statistics.median(r.latency_ms for r in rs), 1),
            "median_latency_ms_when_sent": round(statistics.median(r.latency_ms for r in sent), 1) if sent else None,
            "cloud_calls": sum(r.cloud_calls for r in rs), "bytes_out": sum(r.bytes_out for r in rs),
            "personal_fields_sent": sum(r.personal_fields_sent for r in rs), "wall_s": round(wall, 2)}


def run(write: bool = True, live: bool | None = None, delays: bool | None = None) -> dict:
    qs, part = load_queries(), load_partition()
    res = {"backend": "simulated", "latency": "modelled", "quality": "pending live judge (coverage reported instead)", "modes": {}}
    for m in MODES:
        be = SimBackend(part, mode=m)
        rs = [be.ask(q) for q in qs]
        res["modes"][m] = {
            "median_latency_ms": statistics.median(r.latency_ms for r in rs),
            "cloud_calls": sum(r.cloud_calls for r in rs),
            "cloud_tokens": sum(r.tokens for r in rs),
            "personal_fields_sent": sum(r.personal_fields_sent for r in rs),
            "coverage": round(sum(r.state == q["expected_state"] for r, q in zip(rs, qs)) / len(qs), 3),
            "not_fully_answered": [q["id"] for q, r in zip(qs, rs) if r.state != q["expected_state"]],
        }
    live = LiveBackend.available() if live is None else live
    if live:
        res["live"] = {"no_delay": run_live("0,0")}
        if (os.environ.get("EVAL_DELAYS") == "1") if delays is None else delays:
            res["live"]["default_delay"] = run_live(DEFAULT_DELAY)
        else:
            res["live"]["default_delay"] = "not run (EVAL_DELAYS=1 runs it; it waits through real P6.4 delays)"
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        CHARTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "latency_cost.json").write_text(json.dumps(res, indent=1) + "\n")
        cats = [LABELS[m] for m in MODES]
        mm = res["modes"]
        panels = [
            grouped_bars("Cloud calls for the 20 questions", "Fewer is cheaper and leaks less (simulated)", cats,
                         [("Cloud calls", [mm[m]["cloud_calls"] for m in MODES])]),
            grouped_bars("Personal fields sent to the cloud", "Genotypes, labs, meds, conditions, age (simulated)", cats,
                         [("Personal fields", [mm[m]["personal_fields_sent"] for m in MODES])]),
            grouped_bars("Questions reaching their expected answer", "Coverage, not graded quality (quality judge runs on the live build)", cats,
                         [("Coverage", [mm[m]["coverage"] for m in MODES])], y_max=1.0, pct=True),
        ]
        (CHARTS / "latency_cost.svg").write_text(stacked_panels(panels))
    return res


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
