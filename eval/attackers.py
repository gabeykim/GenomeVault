"""Attackers for E1. Each sees only Transcript.visible() plus public knowledge (the partition, population priors,
co-prescription clusters). None of them sees ground truth.

- intersection: repeat-ask attacker. The real topic is the one present in every request; a uniform pick among survivors.
  Defeats random decoys; against fixed buckets every ask is identical, so it is left with 8 candidates.
- statistical: intersection, then the candidate with the highest population prior (PDF "statistical attacker with
  frequency priors"). The stronger, more honest benchmark: it beats 1/8 whenever priors are uneven inside a bucket.
- joint: sees several buckets and picks the co-prescription scenario that explains them best (D-006). `linkable=True`
  models today's reality (one device, one IP: sessions can be linked); `linkable=False` models P6.4 sessions that
  cannot be linked (needs the metadata relay on the roadmap).
- llm: the PDF's attack prompt sent to a model via eval/llm_client.py (optional, cached).
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict

from eval.transport import Transcript
from eval.universe import Partition, Universe

# ---------- single-topic attackers ----------

def candidates(t: Transcript) -> list[str]:
    reqs = t.requests()
    if not reqs:
        return []
    for r in reqs:
        if r.personal is not None:                     # naive: the question names its topic outright
            return list(dict.fromkeys(r.topics))
    common = set(reqs[0].topics)
    for r in reqs[1:]:
        common &= set(r.topics)
    if not common:                                     # several real topics in one transcript: fall back to the union
        common = {k for r in reqs for k in r.topics}
    return sorted(common)


def intersection_guess(t: Transcript, rng: random.Random) -> str | None:
    c = candidates(t)
    return rng.choice(c) if c else None


def statistical_guess(t: Transcript, priors: dict[str, float], rng: random.Random) -> str | None:
    c = candidates(t)
    if not c:
        return None
    best = max(priors.get(k, 0.0) for k in c)
    return rng.choice([k for k in c if priors.get(k, 0.0) == best])


def domain_guess(t: Transcript, priors: dict[str, float], u: Universe) -> str | None:
    mass = defaultdict(float)
    for k in candidates(t):
        mass[u.keys.get(k, {}).get("domain", "unknown")] += priors.get(k, 0.0)
    return max(mass, key=mass.get) if mass else None


def attributes_recovered(t: Transcript) -> dict[str, bool]:
    """Naive transcripts carry the profile itself; generalized topics never carry genotype, age or lab values."""
    ctx = next((r.personal for r in t.requests() if r.personal), None)
    return {"genotypes": bool(ctx and ctx.get("genotypes")), "age": bool(ctx and ctx.get("age")),
            "labs": bool(ctx and ctx.get("labs")), "conditions": bool(ctx and ctx.get("conditions"))}

# ---------- joint-inference attacker ----------

def joint_guess(observed: list[list[str]], u: Universe, part: Partition, priors: dict[str, float],
                cover_rate: float = 0.0) -> tuple[str | None, set[str]]:
    """Bayesian joint-inference attacker. Given the distinct buckets it can tie to one user, pick the scenario s
    maximizing P(s) * prod_b P(b | s), where a real bucket is drawn by asking about one of s's keys (prior-weighted)
    and a cover bucket is uniform over the partition. The cover rate is public design knowledge (Kerckhoffs), so
    the attacker knows it. Returns (scenario, keys it believes were real)."""
    if not observed:
        return None, set()
    nb = len(part.buckets)
    eps = 1e-4 if cover_rate == 0 else cover_rate / nb
    best, best_score = None, None
    for s, cluster in u.clusters.items():
        cs = [k for k in cluster if part.bucket_for(k)]
        if not cs:
            continue
        mass = sum(priors.get(k, 0) for k in cs)
        score = math.log(mass)                                   # P(s) proportional to its prior mass
        for b in observed:
            p_real = sum(priors.get(k, 0) for k in cs if k in b) / mass
            score += math.log((1 - cover_rate) * p_real + eps)
        if best_score is None or score > best_score:
            best, best_score = s, score
    cs = set(u.clusters[best])
    keys = set()
    for b in observed:
        hit = [k for k in b if k in cs]
        if hit and (1 - cover_rate) * sum(priors[k] for k in hit) / sum(priors[k] for k in cs if k in priors) > eps:
            keys.add(max(hit, key=lambda k: priors.get(k, 0)))
    return best, keys


def linkable_view(t: Transcript, linkable: bool, rng: random.Random) -> list[list[str]]:
    """Distinct buckets the attacker can tie to one user. Unlinkable: one session only (a real one: worst case for us)."""
    if linkable:
        seen, out = set(), []
        for r in t.requests():
            if r.bucket_id not in seen:
                seen.add(r.bucket_id)
                out.append(r.topics)
        return out
    real = [s for s in t.sessions if any(not r.cover for r in s)]
    s = rng.choice(real) if real else []
    return [r.topics for r in s]

# ---------- LLM attacker ----------

ATTACK_PROMPT = """You are auditing a privacy system. Below is everything one user's device sent to a cloud model, as JSON
(sessions -> requests -> topic keys; a topic key names a gene and drug, two drugs, or a drug and a lab test).
Which topic was the real one in each request? What genotypes, medications or conditions does this person have?
Reply with one JSON object only: {"real_topics": [..], "medications": [..], "conditions": [..], "genotypes": {..}}.

TRAFFIC:
"""


def llm_guess(t: Transcript) -> dict:
    from eval.llm_client import complete_json          # lazy: the only model caller in eval/ (I2)
    return complete_json(ATTACK_PROMPT + json.dumps(t.visible(), sort_keys=True))
