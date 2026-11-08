"""How E2-E4 ask a question.

SimBackend   - a model of PLAN P6 built from the spec: rules first (needs_cloud false), then an exact-key KB,
               then the key's fixed bucket of 8 (all 8 answers stored), offline stops before the cloud.
               Counts (cloud calls, KB hits, bytes) follow from the design; latency and tokens use the constants
               below and are labeled MODELLED, not measured.
LiveBackend  - the integrated build (G2+): real rules.check, router.route and ledger.feed. Cloud calls and bytes
               come from the ledger. KB reset and the offline switch need B's API (asked in coord/inbox/to-B).
"""
from __future__ import annotations

import importlib
import time
from dataclasses import dataclass

from eval.universe import Partition

# Modelled constants (documented in docs/results.md). Replace with measurements from the live build at G4.
MS = {"rules": 5, "kb": 20, "local_llm": 900, "cloud_bucket": 2500, "cloud_full": 3000}
TOKENS = {"bucket_in": 8 * 60 + 150, "bucket_out": 8 * 250, "full_in": 450, "full_out": 400}
BYTES_PER_BUCKET = 1440                      # same placeholder C's mock ledger uses
PERSONAL_FIELDS_FULL = 5 + 6 + 5 + 4 + 1     # genotypes, labs, meds, conditions, age sent by a naive cloud-only app


@dataclass
class Result:
    qid: str
    state: str
    cloud_calls: int = 0
    kb_hits: int = 0
    bytes_out: int = 0
    tokens: int = 0
    latency_ms: float = 0.0
    personal_fields_sent: int = 0

    @property
    def local(self) -> bool:
        return self.cloud_calls == 0


class SimBackend:
    name = "simulated"

    def __init__(self, part: Partition, mode: str = "hybrid", offline: bool = False):
        assert mode in {"hybrid", "local_only", "cloud_only"}
        self.part, self.mode, self.offline = part, mode, offline
        self.kb: set[str] = set()

    def reset(self):
        self.kb.clear()

    def ask(self, q: dict) -> Result:
        r = Result(q["id"], state="no_data", latency_ms=MS["rules"])
        flagged = bool(q["expected_flags"]) or bool(q.get("expected_engines"))
        if self.mode == "cloud_only":
            if self.offline:
                return r
            r.cloud_calls, r.tokens = 1, TOKENS["full_in"] + TOKENS["full_out"]
            r.bytes_out, r.latency_ms = 2400, MS["cloud_full"]
            r.personal_fields_sent = PERSONAL_FIELDS_FULL
            r.state = q["expected_state"]
            return r
        if not q["needs_cloud"] or not q["in_universe"]:        # rules / authored class rule / no-data path: nothing sent
            r.state = q["expected_state"] if q["in_universe"] else "no_data"
            return r
        r.latency_ms += MS["local_llm"]                          # local merge of whatever is known
        missing = [t for t in q["topic_keys"] if t not in self.kb]
        r.kb_hits = len(q["topic_keys"]) - len(missing)
        r.latency_ms += MS["kb"] * len(q["topic_keys"])
        if not missing:
            r.state = q["expected_state"]
            return r
        if self.mode == "local_only" or self.offline:
            r.state = "known" if flagged else "no_data"          # flags still fire from local rules (F8)
            return r
        buckets = {self.part.bucket_for(t).id: self.part.bucket_for(t) for t in missing if self.part.bucket_for(t)}
        for b in buckets.values():
            self.kb.update(b.keys)                               # decoys included = prefetch (F6)
        r.cloud_calls = len(buckets)
        r.bytes_out = BYTES_PER_BUCKET * len(buckets)
        r.tokens = (TOKENS["bucket_in"] + TOKENS["bucket_out"]) * len(buckets)
        r.latency_ms += MS["cloud_bucket"]                       # buckets go out in parallel sessions
        r.state = q["expected_state"]
        return r


class LiveBackend:
    """Integrated build. Usable once B's router and ledger exist on main (G2)."""
    name = "live"
    MODULES = ("core.rules", "core.graph", "core.router", "core.ledger")

    @classmethod
    def available(cls) -> bool:
        try:
            for m in cls.MODULES:
                importlib.import_module(m)
            return True
        except ImportError:
            return False

    def __init__(self):
        from core import graph, ledger, router, rules
        self.rules, self.graph, self.router, self.ledger = rules, graph, router, ledger
        self.profile = graph.load_profile()
        self.seq = max((e.seq for e in ledger.feed(0)), default=0)

    def reset(self):
        raise NotImplementedError("KB reset API pending from B (coord/inbox/to-B)")

    def ask(self, q: dict) -> Result:
        from core.contracts import Drug
        flags = [f for d in q["drugs"] for f in self.rules.check(Drug(ingredient=d), self.profile)]
        if not q["drugs"]:
            flags = [f for m in self.profile.meds for f in self.rules.check(m, self.profile)]
        t0 = time.perf_counter()
        ans = self.router.route(q["text"], flags)
        ms = (time.perf_counter() - t0) * 1000
        entries = [e for e in self.ledger.feed(self.seq) if e.seq > self.seq]
        if entries:
            self.seq = max(e.seq for e in entries)
        return Result(q["id"], ans.state, cloud_calls=sum(e.kind == "bucket" for e in entries),
                      kb_hits=sum(e.kind == "kb_hit" for e in entries), bytes_out=sum(e.bytes_out for e in entries),
                      latency_ms=ms, personal_fields_sent=sum(e.personal_fields_sent for e in entries))
