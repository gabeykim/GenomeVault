"""How E2-E4 ask a question.

SimBackend   - a model of PLAN P6 built from the spec: rules first (needs_cloud false), then an exact-key KB,
               then the key's fixed bucket of 8 (all 8 answers stored), offline stops before the cloud.
               Counts (cloud calls, KB hits, bytes) follow from the design; latency and tokens use the constants
               below and are labeled MODELLED, not measured.
LiveBackend  - the integrated build (G2+): real rules.check, router.route and ledger.feed. Cloud calls and bytes
               come from the ledger. Cold KB via core.kb.clear(), offline via core.cloud.set_offline() (B-008).
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
    local_flags: int = 0          # flags A's rules produced for this question
    facts: int = 0                # keyed facts behind the answer (KB or cloud)

    @property
    def local(self) -> bool:
        return self.cloud_calls == 0

    @property
    def unbacked(self) -> bool:
        """Claims knowledge ('known'/'none_listed') with no flag and no fact behind it: breaks I4 (missing = no_data)."""
        return self.state in ("known", "none_listed") and self.local_flags == 0 and self.facts == 0

    @property
    def effective_state(self) -> str:
        """What the user actually gets: local flags count as content even when the router's own answer is no_data."""
        if self.local_flags or (self.state in ("known", "none_listed") and self.facts):
            return "known" if self.state != "none_listed" else "none_listed"
        return "no_data"


def sendable(q: dict, part: Partition) -> list[str]:
    """Partition keys q would send: one per topic that has a fixed bucket (the rest take the no-data path, I5).
    The exact local key picks the bucket when a topic's variants sit in different buckets."""
    out = []
    for local, topic in zip(q["keys"], q["topic_keys"]):
        vk = part.view_key(local, topic)
        if vk is not None and vk not in out:
            out.append(vk)
    return out


# PLAN P5 flag keys (A-003): a flag answers a question only if its exact key is one of the question's keys
FLAG_KEYS = {"X1": {"CYP2C19:poor_metabolizer|clopidogrel"}, "X2": {"clopidogrel|omeprazole"},
             "X3": {"SLCO1B1:decreased_function|simvastatin|dose>20mg"}, "X4": {"lisinopril|potassium>5.0"},
             "X5": {"aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60"}}


def answering_flags(q: dict) -> int:
    """How many expected local flags answer q itself (key among q['keys']); authored class rules answer their own keys."""
    keys = set(q["keys"])
    n = sum(len(FLAG_KEYS.get(f, set()) & keys) for f in q["expected_flags"])
    return n + (len(keys) if q.get("expected_engines") else 0)


def flagged(q: dict) -> bool:
    return answering_flags(q) > 0


def expected_state(q: dict, part: Partition) -> str:
    """queries.json states assume the keys can be sent; recompute for the partition actually loaded."""
    if q["needs_cloud"] and q["topic_keys"] and not sendable(q, part) and not flagged(q):
        return "no_data"
    return q["expected_state"]


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
        is_flagged = flagged(q)
        r.local_flags = answering_flags(q)
        if self.mode == "cloud_only":
            if self.offline:
                return r
            r.cloud_calls, r.tokens = 1, TOKENS["full_in"] + TOKENS["full_out"]
            r.bytes_out, r.latency_ms = 2400, MS["cloud_full"]
            r.personal_fields_sent = PERSONAL_FIELDS_FULL
            r.state = q["expected_state"]
            r.facts = 1 if r.state != "no_data" else 0
            return r
        if not q["needs_cloud"]:                                 # rules / authored class rule / no-data path: nothing sent
            r.state = q["expected_state"]
            return r
        send = sendable(q, self.part)
        if not send:                                             # every key outside the partition: no-data path (I5)
            r.state = "known" if is_flagged else "no_data"
            return r
        r.latency_ms += MS["local_llm"]                          # local merge of whatever is known
        missing = [t for t in send if t not in self.kb]
        r.kb_hits = len(send) - len(missing)
        r.latency_ms += MS["kb"] * len(send)
        if not missing:
            r.state = q["expected_state"]
            r.facts = len(send)
            return r
        if self.mode == "local_only" or self.offline:
            r.state = "known" if is_flagged else "no_data"       # flags still fire from local rules (F8)
            return r
        buckets = {self.part.bucket_for(t).id: self.part.bucket_for(t) for t in missing if self.part.bucket_for(t)}
        for b in buckets.values():
            self.kb.update(b.keys)                               # decoys included = prefetch (F6)
        r.cloud_calls = len(buckets)
        r.bytes_out = BYTES_PER_BUCKET * len(buckets)
        r.tokens = (TOKENS["bucket_in"] + TOKENS["bucket_out"]) * len(buckets)
        r.latency_ms += MS["cloud_bucket"]                       # buckets go out in parallel sessions
        r.state = q["expected_state"]
        r.facts = len(send)
        return r


class LiveBackend:
    """Integrated build. Needs B's router, ledger, kb and cloud (G2). A's rules/graph are used when they exist and
    the mocks in core.interfaces otherwise, like C's app does; `self.mocked` says which."""
    name = "live"
    REQUIRED = ("core.router", "core.ledger", "core.kb", "core.cloud")

    @classmethod
    def available(cls) -> bool:
        try:
            for m in cls.REQUIRED:
                importlib.import_module(m)
            return True
        except ImportError:
            return False

    def __init__(self):
        from core import interfaces, ledger, router
        self.router, self.ledger = router, ledger
        self.mocked = []
        self.check_all = None
        try:
            from core import rules
            self.check = rules.check
            self.check_all = getattr(rules, "check_all", None)
        except ImportError:
            self.check = interfaces.check
            self.mocked.append("rules")
        try:
            from core import graph
            self.profile = graph.load_profile()
        except ImportError:
            self.profile = interfaces.load_profile()
            self.mocked.append("graph")
        self.name = "live" + (f" (mock {', '.join(self.mocked)})" if self.mocked else "")
        self.seq = max((e.seq for e in ledger.feed(0)), default=0)

    def reset(self):
        """Cold KB (B-008): kb.clear() empties the store and deletes the GV_KB_PATH file."""
        from core import kb
        kb.clear()

    def sync_pack(self) -> bool:
        """Fully warm KB (B-010): every in-universe key, logged as cover rows. False if the build lacks it."""
        fn = getattr(self.router, "sync_pack", None)
        if fn is None:
            return False
        fn()
        self.seq = max((e.seq for e in self.ledger.feed(0)), default=0)   # sync rows are not per-question traffic
        return True

    @property
    def offline(self) -> bool:
        from core import cloud
        return not cloud.status()["online"]

    @offline.setter
    def offline(self, value: bool) -> None:
        """B-008: forced offline wins over DEMO=1; router sends nothing and writes no cloud ledger entry."""
        from core import cloud
        cloud.set_offline(True if value else None)

    def ask(self, q: dict) -> Result:
        from core.contracts import Drug
        if q["drugs"]:
            raw = [f for d in q["drugs"] for f in self.check(Drug(ingredient=d), self.profile)]
        elif self.check_all:
            raw = self.check_all(self.profile)
        else:
            raw = [f for m in self.profile.meds for f in self.check(m, self.profile)]
        flags = list({f.key: f for f in raw}.values())   # dedupe by exact key: X5 is four flags sharing one id (A-003)
        t0 = time.perf_counter()
        ans = self.router.route(q["text"], flags)
        ms = (time.perf_counter() - t0) * 1000
        entries = [e for e in self.ledger.feed(self.seq) if e.seq > self.seq]
        if entries:
            self.seq = max(e.seq for e in entries)
        return Result(q["id"], ans.state, cloud_calls=sum(e.kind == "bucket" for e in entries),
                      kb_hits=sum(e.kind == "kb_hit" for e in entries), bytes_out=sum(e.bytes_out for e in entries),
                      latency_ms=ms, personal_fields_sent=sum(e.personal_fields_sent for e in entries),
                      local_flags=sum(f.key in set(q["keys"]) for f in flags), facts=len(ans.facts))
