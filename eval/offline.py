"""E4 offline continuity (PLAN P7, F8): with no network, how many of the 20 questions still get a correct flag or
answer? Cold device (empty KB) vs warm (after one online pass). A question counts as handled when the answer state
is right for the situation: content when something local knows it, and an honest `no_data` (never a guess, I4)
otherwise. Run: python -m eval.offline"""
from __future__ import annotations

import json
from collections import Counter

from eval.backends import LiveBackend, SimBackend
from eval.charts import grouped_bars
from eval.universe import ROOT, load_partition, load_queries

RESULTS, CHARTS = ROOT / "eval" / "results", ROOT / "docs" / "charts"
CATS = ["gene_drug", "drug_drug", "drug_lab", "otc", "open_ended"]


def _pass(be, qs: list[dict]) -> dict:
    rows = {}
    for q in qs:
        r = be.ask(q)
        rows[q["id"]] = {"category": q["category"], "state": r.effective_state, "router_state": r.state,
                         "with_content": r.effective_state != "no_data", "unbacked": r.unbacked,
                         "local_flags": r.local_flags, "facts": r.facts, "cloud_calls": r.cloud_calls}
    return rows


def run(write: bool = True, live: bool | None = None) -> dict:
    qs, part = load_queries(), load_partition()
    live = LiveBackend.available() if live is None else live
    if live:
        be = LiveBackend()
        be.reset()
        be.offline = True
        cold_rows = _pass(be, qs)
        be.offline = False
        _pass(be, qs)                   # one online session fills the KB
        be.offline = True
        warm_rows = _pass(be, qs)
        synced_rows = None
        be.offline = False              # sync_pack fetches nothing while offline (B-010), so go back online first
        be.reset()
        if be.sync_pack():              # B-010 / D-027: whole partition prefetched (same for every user), then offline
            be.offline = True
            synced_rows = _pass(be, qs)
        be.offline = False
        name = be.name
    else:
        cold = SimBackend(part, offline=True)
        cold_rows = _pass(cold, qs)
        warm = SimBackend(part)
        _pass(warm, qs)                 # one online session fills the KB
        warm.offline = True
        warm_rows = _pass(warm, qs)
        synced = SimBackend(part)
        synced.kb.update(part.keys)     # model of B-010 sync_pack: every in-universe key prefetched
        synced.offline = True
        synced_rows = _pass(synced, qs)
        name = "simulated"
    for rows in (cold_rows, warm_rows):
        assert all(r["cloud_calls"] == 0 for r in rows.values()), "offline must send nothing"
    def by_cat(rows):
        c = Counter(r["category"] for r in rows.values() if r["with_content"])
        return {k: c.get(k, 0) for k in CATS}
    total = Counter(q["category"] for q in qs)
    res = {"backend": name, "cold_answered": sum(r["with_content"] for r in cold_rows.values()),
           "warm_answered": sum(r["with_content"] for r in warm_rows.values()), "n": len(qs),
           "cold_by_category": by_cat(cold_rows), "warm_by_category": by_cat(warm_rows), "category_sizes": dict(total),
           "matches_offline_state_cold": sum(cold_rows[q["id"]]["state"] == q["offline_state"] for q in qs),
           "synced_answered": sum(r["with_content"] for r in synced_rows.values()) if synced_rows else None,
           "unbacked_known": sorted({qid for rows in (cold_rows, warm_rows) for qid, r in rows.items() if r["unbacked"]}),
           "cold_rows": cold_rows, "warm_rows": warm_rows}
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        CHARTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "offline.json").write_text(json.dumps(res, indent=1) + "\n")
        labels = ["Gene–drug", "Drug–drug", "Drug–lab", "OTC", "Open-ended"]
        frac = lambda d: [d[c] / total[c] for c in CATS]
        (CHARTS / "offline.svg").write_text(grouped_bars(
            "What still works with Wi-Fi off?",
            f"Share of questions answered with content: cold {res['cold_answered']}/20, warm {res['warm_answered']}/20 (rest get an honest 'no data')",
            labels, [("Cold device (empty KB)", frac(res["cold_by_category"])), ("Warm device (after one session)", frac(res["warm_by_category"]))],
            y_max=1.0, pct=True))
    return res


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in run().items() if not k.endswith("_rows")}, indent=1))
