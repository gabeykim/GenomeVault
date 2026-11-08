"""E1 red team (PLAN P7): can an attacker who sees all outbound traffic recover the real topic, the user's
medications or their condition?

Three conditions (naive / random decoys / fixed buckets) x two deterministic attackers (intersection, statistical)
over N synthetic patients, plus the joint-inference attacker across simultaneous buckets, plus an optional LLM attacker.
Deterministic attackers run 500 trials (free, stable to about +-3 points); the LLM attacker runs 50 (PLAN E1 budget).
Run: python -m eval.redteam [--trials 500] [--asks 3] [--llm]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict

from eval import attackers as A
from eval import transport as T
from eval.charts import grouped_bars
from eval.synth import alex, drugs_in, make_patients, scenario_weights
from eval.universe import ROOT, load_partition, load_universe, priors_for

RESULTS = ROOT / "eval" / "results"
CHARTS = ROOT / "docs" / "charts"
ALEX_Q18 = ["CYP2C19|clopidogrel", "clopidogrel|omeprazole", "SLCO1B1|simvastatin", "lisinopril|potassium"]


def bucket_design_report(part, u, priors) -> dict:
    """Partition-level numbers B can tune against (independent of the trial sample)."""
    total = sum(priors.values())
    rows, stat = [], 0.0
    for b in part.buckets:
        ps = [priors[k] for k in b.keys]
        doms = Counter(u.keys.get(k, {}).get("domain", "unknown") for k in b.keys)
        dom, cnt = doms.most_common(1)[0]
        stat += max(ps) / total
        rows.append({"bucket": b.id, "prior_mass": round(sum(ps) / total, 4), "top_key_share": round(max(ps) / sum(ps), 3),
                     "dominant_domain": dom, "dominant_domain_share": round(cnt / 8, 3)})
    return {"stat_attacker_ceiling": round(stat, 4), "uniform_floor": 0.125, "buckets": rows}


def run_single_topic(n: int, asks: int, seed: int, part, u, priors) -> dict:
    patients = make_patients(n, seed, u, part, n_keys=1)
    rng = random.Random(seed + 1)
    conds = {
        "naive": lambda p: T.naive(p, asks),
        "random_decoys": lambda p: T.random_decoys(p, part, rng, asks),
        "random_decoys_1ask": lambda p: T.random_decoys(p, part, rng, 1),
        "fixed_buckets": lambda p: T.fixed_buckets(p, part, rng, asks),
    }
    out = {}
    for name, make in conds.items():
        m = defaultdict(int)
        for p in patients:
            t = make(p)
            real = p.topic_keys[0]
            gi, gs = A.intersection_guess(t, rng), A.statistical_guess(t, priors, rng)
            m["intersection"] += gi == real
            m["statistical"] += gs == real
            m["domain"] += A.domain_guess(t, priors, u) == u.keys[real]["domain"]
            m["med_inferred"] += bool(gs) and all(d in p.meds for d in drugs_in(gs))
            m["genotype_leaked"] += A.attributes_recovered(t)["genotypes"]
        out[name] = {k: round(v / n, 3) for k, v in m.items()}
    dom_prior = Counter()
    for p in patients:
        dom_prior[u.keys[p.topic_keys[0]]["domain"]] += 1
    out["_baselines"] = {"uniform_1_in_8": 0.125, "domain_majority_guess": round(dom_prior.most_common(1)[0][1] / n, 3)}
    return out


def run_joint(n: int, seed: int, part, u, priors, cover_per_real: int = 2) -> dict:
    patients = make_patients(n, seed + 100, u, part, n_keys=(2, 4), min_scenario_keys=2)
    rng = random.Random(seed + 2)
    conds = {
        "same_session": dict(separate_sessions=False, cover_per_real=0, linkable=True),
        "separate_cover_linkable": dict(separate_sessions=True, cover_per_real=cover_per_real, linkable=True),
        "separate_cover_unlinkable": dict(separate_sessions=True, cover_per_real=cover_per_real, linkable=False),
    }
    out = {}
    for name, c in conds.items():
        sc, recall = 0, 0.0
        for p in patients:
            t = T.fixed_buckets(p, part, rng, 1, c["separate_sessions"], c["cover_per_real"])
            cr = c["cover_per_real"] / (1 + c["cover_per_real"])
            scen, keys = A.joint_guess(A.linkable_view(t, c["linkable"], rng), u, part, priors, cr)
            sc += scen == p.scenario
            recall += len(keys & set(p.topic_keys)) / len(p.topic_keys)
        out[name] = {"scenario": round(sc / n, 3), "key_recall": round(recall / n, 3)}
    w = scenario_weights(u, part, 2)
    out["_baselines"] = {"scenario_majority_guess": round(max(w.values()) / sum(w.values()), 3), "n_scenarios": len(w)}
    # Alex's demo question S4 (Q18): four buckets
    a = alex(ALEX_Q18)
    alex_out = {}
    for name, c in conds.items():
        hits = 0
        for _ in range(20):
            t = T.fixed_buckets(a, part, rng, 1, c["separate_sessions"], c["cover_per_real"])
            cr = c["cover_per_real"] / (1 + c["cover_per_real"])
            hits += A.joint_guess(A.linkable_view(t, c["linkable"], rng), u, part, priors, cr)[0] == a.scenario
        alex_out[name] = round(hits / 20, 2)
    out["alex_q18_scenario_recovered"] = alex_out
    out["alex_note"] = ("Do not quote Alex alone: cardiac_post_stent is the most common scenario in the synthetic priors, "
                        "so a blind guess already says cardiac. The population numbers vs scenario_majority_guess are the honest measure.")
    return out


def run_llm(n: int, asks: int, seed: int, part, u) -> dict:
    from eval.llm_client import LLMUnavailable, model_name
    patients = make_patients(n, seed + 200, u, part, n_keys=1)
    rng = random.Random(seed + 3)
    out = {"model": model_name()}
    try:
        for name, make in {"naive": lambda p: T.naive(p, asks), "random_decoys": lambda p: T.random_decoys(p, part, rng, asks),
                           "fixed_buckets": lambda p: T.fixed_buckets(p, part, rng, asks)}.items():
            hit = 0
            for p in patients:
                g = A.llm_guess(make(p))
                topics = g.get("real_topics") or []
                hit += bool(topics) and topics[0] == p.topic_keys[0]
            out[name] = round(hit / n, 3)
        out["status"] = "ran"
    except (LLMUnavailable, ValueError) as e:
        out["status"] = f"skipped: {e}"
    return out


def run(trials: int = 500, asks: int = 3, seed: int = 7, llm: bool = False, llm_trials: int = 50, write: bool = True) -> dict:
    part, u = load_partition(), load_universe()
    priors = priors_for(part, u)
    res = {"partition": part.source, "partition_version": part.version, "universe": u.version,
           "trials": trials, "asks": asks, "seed": seed, "mode": "simulated transport (P6 model; real capture after G2)",
           "single_topic": run_single_topic(trials, asks, seed, part, u, priors),
           "joint": run_joint(trials, seed, part, u, priors),
           "bucket_design": bucket_design_report(part, u, priors),
           "llm": run_llm(llm_trials, asks, seed, part, u) if llm else {"status": "not requested (pass --llm or EVAL_LLM=1)"}}
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        CHARTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "redteam.json").write_text(json.dumps(res, indent=1) + "\n")
        st = res["single_topic"]
        cats = ["Naive\n(full question)", "Random decoys\n(fresh each ask)", "Fixed buckets\n(GenomeVault)"]
        keys = ["naive", "random_decoys", "fixed_buckets"]
        series = [("Repeat-ask attacker", [st[k]["intersection"] for k in keys]),
                  ("Statistical attacker", [st[k]["statistical"] for k in keys])]
        if res["llm"].get("status") == "ran":
            series.append((f"LLM attacker", [res["llm"][k] for k in keys]))
        (CHARTS / "redteam.svg").write_text(grouped_bars(
            "Can an attacker find the real question?",
            f"Share of {trials} synthetic patients whose real topic was guessed from outbound traffic ({asks} asks each)",
            cats, series, y_max=1.0, pct=True, ref=(0.125, "1 in 8 (best possible with k = 8)")))
        j = res["joint"]
        jk = ["same_session", "separate_cover_linkable", "separate_cover_unlinkable"]
        (CHARTS / "joint.svg").write_text(grouped_bars(
            "Can simultaneous buckets reveal the condition?",
            f"Joint-inference attacker, {trials} synthetic patients asking about 2-4 related drugs at once",
            ["One session", "Separate sessions + cover\n(same device, linkable)", "Separate sessions + cover\n(unlinkable, needs relay)"],
            [("Condition guessed", [j[k]["scenario"] for k in jk]), ("Real topics recovered", [j[k]["key_recall"] for k in jk])],
            y_max=1.0, pct=True, ref=(j["_baselines"]["scenario_majority_guess"], "guess the most common condition")))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=500)
    ap.add_argument("--asks", type=int, default=3)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    r = run(a.trials, a.asks, a.seed, a.llm)
    print(json.dumps({k: r[k] for k in ("partition", "single_topic", "joint", "llm")}, indent=1))
    print("bucket design: stat-attacker ceiling", r["bucket_design"]["stat_attacker_ceiling"])
