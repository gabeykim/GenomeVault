"""E3 latency, cloud usage and answer coverage (PLAN P7): local-only vs cloud-only vs hybrid on the 20 questions.

Simulated: counts follow from the design; latency/tokens use MODELLED constants (eval/backends.py).
Quality 1-5 against the reference answers needs a judge model (eval/llm_client.py) on the live build; until then
the table reports coverage (share of questions reaching their expected answer state), clearly labeled as such.
Run: python -m eval.latency_cost"""
from __future__ import annotations

import json
import statistics

from eval.backends import SimBackend
from eval.charts import grouped_bars, stacked_panels
from eval.universe import ROOT, load_partition, load_queries

RESULTS, CHARTS = ROOT / "eval" / "results", ROOT / "docs" / "charts"
MODES = ["local_only", "cloud_only", "hybrid"]
LABELS = {"local_only": "Local only", "cloud_only": "Cloud only\n(naive)", "hybrid": "Hybrid\n(GenomeVault)"}


def run(write: bool = True) -> dict:
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
        }
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
