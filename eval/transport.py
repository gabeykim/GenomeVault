"""What an observer of all outbound traffic sees, per red-team condition (E1).

This is a SIMULATION of P6 steps 3-6 built from the PLAN, used until B's router merges. `run_all` labels
results "simulated" until it can capture real outbound traffic (see eval/backends.py).

A transcript is a list of sessions; a session is a list of requests; a request is the list of topic keys sent
together (plus, in the naive condition, the full personal context). Only keys inside the partition are ever sent (I5).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from eval.synth import Patient
from eval.universe import Partition


@dataclass
class Request:
    topics: list[str]
    bucket_id: str | None = None
    personal: dict | None = None          # naive condition only
    cover: bool = False                    # ground truth, never shown to attackers


@dataclass
class Transcript:
    sessions: list[list[Request]] = field(default_factory=list)

    def requests(self) -> list[Request]:
        return [r for s in self.sessions for r in s]

    def visible(self) -> list[list[dict]]:
        """What the attacker gets: no ground-truth fields."""
        out = []
        for s in self.sessions:
            out.append([{k: v for k, v in (("bucket_id", r.bucket_id), ("topics", r.topics), ("context", r.personal)) if v is not None}
                        for r in s])
        return out


def naive(p: Patient, asks: int = 1) -> Transcript:
    ctx = {"age": p.age, "genotypes": p.genotypes, "meds": p.meds, "conditions": p.conditions, "labs": p.labs}
    return Transcript([[Request(topics=list(p.topic_keys), personal=ctx) for _ in range(asks)]])


def random_decoys(p: Patient, part: Partition, rng: random.Random, asks: int = 3, k: int = 8) -> Transcript:
    """Generalized topic + 7 decoys drawn fresh at random for every ask (the scheme D-003 rejects)."""
    universe = part.keys
    reqs = []
    for _ in range(asks):
        for key in p.topic_keys:
            decoys = rng.sample([x for x in universe if x != key], k - 1)
            topics = decoys + [key]
            rng.shuffle(topics)
            reqs.append(Request(topics=topics))
    return Transcript([reqs])


def fixed_buckets(p: Patient, part: Partition, rng: random.Random, asks: int = 1, separate_sessions: bool = False,
                  cover_per_real: int = 0) -> Transcript:
    """Generalized topic travels inside its fixed bucket of 8 (I5). Optionally P6.4 separate sessions and P6.6 cover buckets."""
    real = []
    for _ in range(asks):
        seen = set()
        for key in p.topic_keys:
            b = part.bucket_for(key)
            if b is None or b.id in seen:          # out of universe: nothing sent; same bucket twice: dedupe
                continue
            seen.add(b.id)
            real.append(Request(topics=list(b.keys), bucket_id=b.id))
    cover = [Request(topics=list(b.keys), bucket_id=b.id, cover=True)
             for b in (rng.choice(part.buckets) for _ in range(cover_per_real * len(real)))]
    reqs = real + cover
    rng.shuffle(reqs)
    if separate_sessions:
        return Transcript([[r] for r in reqs])
    return Transcript([reqs])
