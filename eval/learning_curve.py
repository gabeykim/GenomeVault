"""E2 learning curve (PLAN P7): run the 20 scripted questions in order from an empty KB; plot cloud calls per
question and the cumulative share answered locally. Run: python -m eval.learning_curve"""
from __future__ import annotations

import json

from eval.backends import LiveBackend, SimBackend
from eval.charts import grouped_bars, line_chart, stacked_panels
from eval.universe import ROOT, load_partition, load_queries

RESULTS, CHARTS = ROOT / "eval" / "results", ROOT / "docs" / "charts"


def run(backend=None, write: bool = True) -> dict:
    qs = load_queries()
    be = backend or SimBackend(load_partition())
    rows, local = [], 0
    for i, q in enumerate(qs, 1):
        r = be.ask(q)
        local += r.local
        rows.append({"q": q["id"], "category": q["category"], "cloud_calls": r.cloud_calls, "kb_hits": r.kb_hits,
                     "bytes_out": r.bytes_out, "state": r.state, "cum_local_share": round(local / i, 3)})
    first, last = rows[:5], rows[-5:]
    res = {"backend": be.name, "rows": rows, "total_cloud_calls": sum(r["cloud_calls"] for r in rows),
           "local_share": round(local / len(qs), 3),
           "cloud_calls_first5": sum(r["cloud_calls"] for r in first), "cloud_calls_last5": sum(r["cloud_calls"] for r in last),
           "repeat_q19_is_local": next(r for r in rows if r["q"] == "Q19")["cloud_calls"] == 0}
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        CHARTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "learning_curve.json").write_text(json.dumps(res, indent=1) + "\n")
        ids = [r["q"] for r in rows]
        top = grouped_bars("Cloud calls per question", f"20 scripted questions in order, empty knowledge base at start ({be.name})",
                           ids, [("Buckets sent", [r["cloud_calls"] for r in rows])], y_max=max(4, max(r["cloud_calls"] for r in rows)),
                           value_labels=False)
        bottom = line_chart("Share answered on device so far", "Cumulative; rules, knowledge-base hits and the no-data path send nothing",
                            ids, [("Answered locally", [r["cum_local_share"] for r in rows])], y_max=1.0)
        (CHARTS / "learning_curve.svg").write_text(stacked_panels([top, bottom]))
    return res


if __name__ == "__main__":
    be = LiveBackend() if LiveBackend.available() else None
    print(json.dumps({k: v for k, v in run(be).items() if k != "rows"}, indent=1))
