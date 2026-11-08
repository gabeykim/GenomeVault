# Agent B — privacy-router

**Mission:** decide what leaves the device and guarantee it reveals nothing (F4–F6, F8, M5–M8).
**Owns:** `core/router.py`, `core/generalize.py`, `core/decoys.py`, `core/kb.py`, `core/cloud.py`, `core/ledger.py`, `core/validator.py`, `data/buckets/`, `tests/B/`
**Provides to others:** `router.route`, `kb.get`, `ledger.feed`, demo-mode cloud replay.
**Depends on:** A's flags (mock until G1).

## Queue

1. `data/buckets/v1.json`: partition of a pair-key universe (≥ 64 keys, includes Alex's keys and `clopidogrel|pantoprazole`) into groups of 8. Done: every key in exactly one bucket.
2. `generalize.py`: Flag → Topics phrased for all phenotypes / lab bands, one concept each. Done: no value from Alex's profile appears in any Topic.
3. `validator.py`: outbound leakage check (I3) + output check (every drug pair and number in an answer comes from a keyed Fact).
4. `cloud.py`: one session per bucket; model from env var; returns `Fact(tier="cloud")`; `DEMO=1` replays `mocks/cloud_cache/`.
5. `ledger.py`: entry per send; `feed(since)` for C.
6. `router.route()` implementing P6 steps 1–5, 7, 8. Done: one question end to end. **Gate G2.**
7. `kb.py`: exact-key store with tier and expiry; stores all 8 bucket answers. Done: repeat question is a KB hit, 0 bytes.
8. Separate sessions, random delays, cover buckets (P6.4, P6.6). **Gate G3.**
9. Offline mode: no network → steps 1–2 only, `no_data` otherwise.

**Stretch:** bulk knowledge-pack sync.
