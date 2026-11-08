"""G4 gate check (PLAN P9): every claim the pitch makes, checked against the results `make eval` just wrote.

    python -m eval.gate          # after `make eval`; exit 1 if any claim FAILs

PASS: the build backs the claim. FAIL: it doesn't; don't quote it. WARN: it holds, but not on the build G4 asks for
(for example simulated rather than live), or a known gap is open. Results go to eval/results/gate.json and the
top of docs/results.md.
"""
from __future__ import annotations

import json
import sys

from eval.universe import ROOT

RESULTS = ROOT / "eval" / "results"


def _load(name: str) -> dict | None:
    f = RESULTS / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else None


def check(rt: dict | None = None, lc: dict | None = None, lat: dict | None = None, off: dict | None = None,
          wd: dict | None = None) -> list[dict]:
    rt, lc, lat, off, wd = (rt or _load("redteam"), lc or _load("learning_curve"), lat or _load("latency_cost"),
                            off or _load("offline"), wd or _load("wording"))
    out = []

    def add(cid, claim, status, value):
        out.append({"id": cid, "claim": claim, "status": status, "value": value})

    if not rt:
        add("G0", "make eval has run", "FAIL", "eval/results/redteam.json missing")
        return out
    st, j, ps = rt["single_topic"], rt["joint"], rt.get("partition_stats", {})
    fb = st["fixed_buckets"]
    real = rt["partition"].startswith("real")
    live = bool(lc) and lc.get("backend", "").startswith("live")
    add("P1", "Evals ran on B's real partition", "PASS" if real else "WARN", rt["partition"])
    add("P2", "E2/E4 ran on the integrated build", "PASS" if live else "WARN", lc.get("backend") if lc else "missing")
    add("E1a", "Naive sending leaks the real question (the attack is real)",
        "PASS" if st["naive"]["intersection"] >= 0.9 else "FAIL", f"{st['naive']['intersection']:.0%}")
    add("E1b", "Random decoys fail once a question repeats",
        "PASS" if st["random_decoys"]["intersection"] >= 0.8 else "FAIL", f"{st['random_decoys']['intersection']:.0%}")
    add("E1c", "Fixed buckets hold a repeat-ask attacker near 1 in 8",
        "PASS" if fb["intersection"] <= 0.20 else "FAIL", f"{fb['intersection']:.0%}")
    add("E1d", "Statistical attacker stays near the design ceiling",
        "PASS" if fb["statistical"] <= rt["bucket_design"]["stat_attacker_ceiling"] + 0.05 else "WARN",
        f"{fb['statistical']:.0%} (ceiling {rt['bucket_design']['stat_attacker_ceiling']:.0%})")
    add("I3a", "No genotype, age or lab value leaves in generalized traffic",
        "PASS" if fb["genotype_leaked"] == 0 and st["random_decoys"]["genotype_leaked"] == 0 else "FAIL",
        f"{fb['genotype_leaked']:.0%}")
    splits = ps.get("phenotype_split_topics") or {}
    pv = fb.get("phenotype_via_bucket", 0)
    add("I3b", "Bucket identity doesn't reveal a phenotype", "PASS" if not splits and pv == 0 else "FAIL",
        f"{len(splits)} split topics, {pv:.1%} of patients")
    base = j["_baselines"]["scenario_majority_guess"]
    add("D-006", "Separate sessions + cover bring condition guessing near a blind guess",
        "PASS" if j["separate_cover_linkable"]["scenario"] <= base + 0.12 else "FAIL",
        f"{j['separate_cover_linkable']['scenario']:.0%} vs blind {base:.0%} (one session {j['same_session']['scenario']:.0%})")
    if lc:
        add("E2a", "Fewer cloud calls than questions", "PASS" if lc["total_cloud_calls"] < len(lc["rows"]) else "WARN",
            f"{lc['total_cloud_calls']} calls / {len(lc['rows'])} questions")
        add("E2b", "A related follow-up (Q19) is answered locally", "PASS" if lc["repeat_q19_is_local"] else
            ("WARN" if live else "FAIL"), "yes" if lc["repeat_q19_is_local"] else "no (live: needs the recorded demo cache, D-019)")
    if lat:
        h = lat["modes"]["hybrid"]
        add("E3a", "Hybrid sends no personal fields", "PASS" if h["personal_fields_sent"] == 0 else "FAIL", h["personal_fields_sent"])
        add("E3b", "Hybrid uses the cloud less than cloud-only", "PASS" if h["cloud_calls"] < lat["modes"]["cloud_only"]["cloud_calls"] else "FAIL",
            f"{h['cloud_calls']} vs {lat['modes']['cloud_only']['cloud_calls']}")
        lv = (lat.get("live") or {}).get("no_delay")
        if lv:
            add("E3c", "Live build sends no personal fields", "PASS" if lv["personal_fields_sent"] == 0 else "FAIL", lv["personal_fields_sent"])
    if off:
        add("E4a", "Offline keeps working (warm >= cold > 0)",
            "PASS" if off["warm_answered"] >= off["cold_answered"] > 0 else "FAIL", f"cold {off['cold_answered']}/20, warm {off['warm_answered']}/20")
        add("E4b", "Offline answers are the honest expected states",
            "PASS" if off["matches_offline_state_cold"] == off["n"] else "WARN", f"{off['matches_offline_state_cold']}/{off['n']}")
    unbacked = set((off or {}).get("unbacked_known", []))
    lv = ((lat or {}).get("live") or {}).get("no_delay")
    if isinstance(lv, dict):
        unbacked |= set(lv.get("unbacked_known", []))
    add("I4", "No answer claims knowledge it doesn't have (missing = no_data)",
        "PASS" if not unbacked else "FAIL",
        "none" if not unbacked else f"'known' with no flag or fact: {', '.join(sorted(unbacked))}")
    if wd and wd.get("status") == "ran":
        plain = wd["by_family"].get("plain", {"caught": 0, "of": 1})
        add("I7a", "The wording filter catches plain 'safe' and start/stop wording",
            "PASS" if plain["caught"] == plain["of"] else "FAIL", f"{plain['caught']}/{plain['of']}")
        add("I7b", "The wording filter catches rephrased attacks",
            "PASS" if wd["caught"] >= 0.9 * wd["should_reject"] else "WARN", f"{wd['caught']}/{wd['should_reject']}")
    else:
        add("I7a", "The wording filter catches plain 'safe' and start/stop wording", "WARN",
            (wd or {}).get("status", "not run"))
    return out


def summary(rows: list[dict]) -> dict:
    return {s: sum(r["status"] == s for r in rows) for s in ("PASS", "WARN", "FAIL")}


def main() -> int:
    rows = check()
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "gate.json").write_text(json.dumps({"summary": summary(rows), "checks": rows}, indent=1) + "\n")
    w = max(len(r["claim"]) for r in rows)
    for r in rows:
        print(f"{r['status']:4}  {r['id']:6} {r['claim']:<{w}}  {r['value']}")
    s = summary(rows)
    print(f"\nG4 gate: {s['PASS']} pass, {s['WARN']} warn, {s['FAIL']} fail")
    return 1 if s["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
