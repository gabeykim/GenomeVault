# Agent B — impact log (append only)

Entries use coord/templates/impact-report.md and are numbered B-001, B-002, ...

### B-001 · 2026-11-08 13:24 · commit `0a8596e` · PLAN v1.1

- **Change:** Added `data/buckets/v1.json` (fixed partition: 96 keys in 12 buckets of 8), `core/decoys.py` (`load_buckets`, `bucket_for`, `universe`, `kind_of`; validates the partition on load), and `tests/B/` (10 tests). PR #2.
- **Why:** BRIEF B queue item 1. The router (queue 6) sends `bucket_for(key)` and stores all 8 answers.
- **Class:** Refines
- **Plan:** advances F4, M5, P6.5, I5; refines P6.5
- **Refinements:** (1) Each bucket holds one key family only (gene–drug, drug–lab, or drug–drug), so the family doesn't point at the real key. Buckets b01–b02 are gene–drug, b03–b04 drug–lab, b05–b12 drug–drug. (2) Each bucket mixes therapeutic areas (oncology, psych, ID, transplant, cardio...) so the bucket alone does not reveal a condition. (3) Keys are sorted within a bucket so position does not hint at which one is real. (4) No bucket holds more than 2 of Alex's drug pairs. (5) `clopidogrel|omeprazole` (b05) and `clopidogrel|pantoprazole` (b06) are in different buckets, so asking about omeprazole does not pre-fill the pantoprazole key in the KB (keeps the S6 no-extrapolation beat clean). (6) A key outside the universe has no bucket: the router will return `no_data` for it, never invent decoys (I4, I5). (7) New partitions ship as new version files (`v2.json`); `v1` is never edited after G2.
- **Contract impact:** none (uses existing `Bucket`)
- **Affects:** A: bucket keys must equal A's exact flag keys. I used the mock keys for X1–X4 and guessed X5 as `aspirin|ibuprofen`, `clopidogrel|ibuprofen`, `ibuprofen|lisinopril`, `ibuprofen|egfr<60` → send me the real X5 keys and lab-band spelling before G2. D: E1 red team can load `core.decoys.load_buckets()` → none. C: none.
- **Demo impact:** S4 (the 8 keys of the bucket that leaves are real, fixed members), S6 (pantoprazole stays a separate key).
- **Tests:** `make test` → 14 passed; `check_ownership.py` → ok; `check_network.sh` → ok
- **Next:** queue item 2, `generalize.py` (Flag → outbound-safe Topics)

### B-002 · 2026-11-08 13:45 · commit `5813ebb` · PLAN v1.1

- **Change:** Added `core/generalize.py` (`topic_for_key(key) -> Topic`, `generalize(flag) -> list[Topic]`) and `tests/B/test_generalize.py` (197 tests, parametrized over all 96 bucket keys). PR #2 updated.
- **Why:** BRIEF B queue item 2. The router (queue 6) turns each of the 8 bucket keys into one Topic and sends only `Topic.text`.
- **Class:** Refines
- **Plan:** advances F4, M5, P6.3, P6.4, I3; refines P6.3
- **Refinements:** (1) One Topic per exact key (one concept each, P6.4). `Topic.key` stays the exact key, used only on-device for KB storage; only `Topic.text` goes out. (2) Gene–drug text names the gene and asks about every phenotype of its family (metabolizer, transporter function, sensitivity, carrier status, enzyme activity); the patient's phenotype is never singled out. (3) Drug–lab text names the lab and asks across low, normal and high; the threshold number in the key is dropped. (4) Dose-conditioned keys ask "across the dose range"; no dose number is sent. (5) Topic text contains no digits except inside gene symbols (CYP2C19), and no `<`, `>` or `*`. (6) Allergy flags generalize to `[]`: the allergy list is personal, so they are never sent and are answered locally.
- **Contract impact:** none (uses existing `Topic`)
- **Affects:** C: none. D: for E1 transcripts, the outbound text for a key is `core.generalize.topic_for_key(key).text`, and all 8 keys in a bucket get the same template, so the wording does not single out the real key → none required. A: drug–lab keys must look like `drug|lab>N` / `drug|lab<N` (lab token lowercase) or `topic_for_key` raises → please keep that spelling.
- **Demo impact:** S4 (the ledger shows these 8 generalized questions leaving).
- **Tests:** `make test` → 211 passed; `check_ownership.py` → ok
- **Next:** queue item 5 `ledger.py` + queue 3 `validator.py` (C needs `ledger.feed` and the output checker for G2), then `cloud.py` and `router.route`.

### B-003 · 2026-11-08 14:05 · commit `b1d1e1b` · PLAN v1.1

- **Change:** Added `core/ledger.py`: `record(kind, bucket_id=None, texts=None) -> LedgerEntry`, `feed(since) -> list[LedgerEntry]` (entries with `seq > since`), `totals()`, `outbound(seq) -> list[str]`, `reset()`. Added `tests/B/test_ledger.py` (12 tests). PR #2 updated.
- **Why:** BRIEF B queue item 5. C polls `ledger.feed` for the live ledger (F5, S3/S4); the router (queue 6) will write every entry through `record`.
- **Class:** Refines
- **Plan:** advances F5, M7, P6.8, I3; refines P6.8
- **Refinements:** (1) `seq` starts at 1 and strictly increases; thread-safe. (2) Only `bucket` / `cover` may have `bytes_out > 0`; they must name a `bucket_id` and the exact texts sent; `kb_hit`, `local_only`, `blocked` are always 0 bytes. (3) `bytes_out` = UTF-8 bytes of the texts actually sent. (4) `personal_fields_sent > 0` is refused (raises): a leaky send is recorded as `blocked`, never as sent (I3). (5) The exact outbound texts are kept on-device and exposed by `outbound(seq)` so the UI can show what left (S4); `LedgerEntry` is unchanged. (6) In-memory by default; if env var `GV_LEDGER_PATH` is set, entries persist to that JSONL file and reload on start. (7) No new kinds; the five in `LedgerEntry` stay.
- **Contract impact:** none (uses existing `LedgerEntry`; `feed` matches CONTRACTS)
- **Affects:** C: once PR #2 merges, `app.py` can stop writing mock entries and import `core.ledger.feed`. Optional extras: `ledger.totals()` (instead of summing `feed(0)`) and `ledger.outbound(seq)` (the 8 generalized questions for a bucket entry). A, D: none.
- **Demo impact:** S3 ("0 bytes sent" comes from `totals()["bytes_out"]`), S4 (ledger shows the bucket's 8 outbound questions).
- **Tests:** `make test` → 223 passed; `check_ownership.py` → ok; `check_network.sh` → ok
- **Next:** queue 3 `validator.py` (leakage check + `check_output`), then queue 4 `cloud.py` and queue 6 `router.route` for G2 (16:00).

### B-004 · 2026-11-08 13:33 · commit `c0f4828` · PLAN v1.1

- **Change:** Added `core/validator.py`: `leaks(text, profile, allow=()) -> list[str]`, `check_outbound(texts, profile, allow=()) -> bool`, `check_output(text, facts) -> bool`, `numbers_in(text)`. Added `tests/B/test_validator.py` (24 tests). PR #2 updated.
- **Why:** BRIEF B queue item 3. The router (queue 6) runs `check_outbound` on the 8 Topic texts right before every send (P6.7) and records `blocked` on failure; C's `merge.personalize` calls `check_output` on the general answer text (agreed in 20261108-1345-from-B-g2-interfaces.md / C's 1331 reply).
- **Class:** Refines
- **Plan:** advances F4, M5, P6.7, I3, I4; refines M5 (leak and output rules)
- **Refinements:** (1) Outbound text is blocked if it contains any standalone number (digits not glued to a letter: catches doses, lab values, dates, ages, `*2/*2`; gene symbols like CYP2C19 pass), any star allele, or any profile genotype, phenotype (`poor_metabolizer` or `poor metabolizer`), condition or allergy, case-insensitive on word boundaries. (2) `allow` admits terms that are the bucket's own drug ingredients (public content of the fixed bucket, I5); it never waives the number rule. (3) All 96 bucket Topics pass (tested). (4) `check_output`: every number in the text must appear in some fact's text or key; drugs are recognised from the bucket universe plus fact keys; any two drugs in one sentence must both be named by a single fact (key or text). So an omeprazole fact cannot back a pantoprazole claim (S6, I4).
- **Contract impact:** none (`check_output` signature as agreed with C)
- **Affects:** C: `core/validator.py` exists on PR #2; merge's lookup will find it once merged → none required. Note: for `no_data` the router's `Answer.text` will not name the drug pair, so it passes `check_output` with `facts=[]`. A, D: none (D may reuse `validator.leaks` in E1 to assert 0 personal fields in transcripts).
- **Demo impact:** S4 (ledger `personal_fields_sent` stays 0 because leaky sends become `blocked`), S6 (pantoprazole answer cannot borrow omeprazole facts).
- **Tests:** `make test` → exit 0, 247 passed; `check_ownership.py` → ok; `check_network.sh` → ok
- **Next:** queue 4 `cloud.py` (DEMO=1 replays `mocks/cloud_cache/`), then queue 6 `router.route` for G2 (16:00).

### B-005 · 2026-11-08 13:50 · commit `54b170c` · PLAN v1.1

- **Change:** Added `core/cloud.py`: `ask_bucket(bucket, topics) -> list[Fact]`, `CloudUnavailable`, `load_cache()`, `record(out_dir)` (also `python -m core.cloud record <dir>`). Added `tests/B/test_cloud.py` (12 tests, network mocked with `httpx.MockTransport`). PR #2 updated.
- **Why:** BRIEF B queue item 4; the router (queue 6, G2) calls `ask_bucket` after the leakage check passes.
- **Class:** Refines
- **Plan:** advances F4, M8, P6.4 (separate sessions, one concept per request), P6.5 (all 8 answers returned), I2, I6, I8; refines M8
- **Refinements:** (1) Each `ask_bucket` call opens a fresh httpx client and closes it after; each Topic is a single-turn request carrying only the Topic text. `ask_bucket` takes only a Bucket and Topics (no Profile) and refuses topics outside the bucket. (2) Env vars: `GV_CLOUD_MODEL` (default `claude-sonnet-5-5`), `ANTHROPIC_API_KEY`, `GV_CLOUD_URL`, `GV_CLOUD_TTL_DAYS` (default 30), `GV_CLOUD_CACHE`, `DEMO=1`. (3) Cloud facts: `tier="cloud"`, `source="cloud:<model>"` (live) or `"cloud-cache:<version>"` (demo), expire 30 days after fetch (I6). (4) Demo cache format: any `*.json` in `mocks/cloud_cache/`, each `{exact key: answer text}`. A key missing from the cache gets no Fact, which the router turns into `no_data` (I4). (5) No key, network down or HTTP error all raise `CloudUnavailable` (the router falls back; queue 9). (6) The system prompt forbids "safe" and start/stop advice (I7).
- **Contract impact:** none (cloud.py is internal to B; no contracts.py change)
- **Affects:** I: `mocks/cloud_cache/` is empty and integrator-owned, so DEMO=1 currently returns no cloud facts (every cloud question becomes `no_data`). Please populate it before G2/G3 with `ANTHROPIC_API_KEY=... python -m core.cloud record mocks/cloud_cache` (writes 12 files, b01..b12), or tell me to hand you the JSON. C, D: none now; demo-mode answers depend on that cache.
- **Demo impact:** S4 (cloud answers in demo come from the cache), I8 (demo makes no network calls; tested).
- **Tests:** `make test` → exit 0, 259 passed; `check_network.sh` → ok
- **Next:** queue 6 `router.route` (P6 steps 1–5, 7, 8) for G2 (16:00).

### B-006 · 2026-11-08 14:10 · commit `aca7eb9` · PLAN v1.1

- **Change:** Added `core/router.py`: `route(question, flags) -> Answer` (contract signature unchanged), plus `tests/B/test_router.py` (10 tests). PR #2 updated.
- **Why:** BRIEF B queue item 6, Gate G2 (one question end to end with live ledger).
- **Class:** Advances
- **Plan:** advances F4, F5, M5, P6.1–5, P6.7, P6.8, I3, I4, I5, G2; refines P6.1, P6.2
- **Refinements:** (1) Keys asked = keys of flags with `needs_cloud=True` (allergy flags never; they generalize to nothing), plus drug–drug pair keys for known drugs the user names in the question (parsed on device; the question text itself never leaves). (2) No such key → one `local_only` entry, `Answer(state="known", text=router.LOCAL_TEXT, facts=[])`. (3) Each key's whole fixed bucket is sent once per route call (shared buckets are not re-sent); all 8 answers go to the KB once `kb.py` lands (queue 7; until then step 2 always misses). (4) Leakage check runs on all 8 Topic texts with the bucket's own drug names allowed; any hit → one `blocked` entry, 0 bytes, nothing sent. (5) `CloudUnavailable` (offline, no key) → no ledger entry (nothing left), and the key is `no_data` (queue 9 refines). (6) Key outside the universe → never sent, `no_data`. (7) `state="known"` if any asked key has a Fact, else `no_data` with `router.NO_DATA_TEXT` ("a missing entry does not mean no interaction"). `Answer.text` = asked facts' texts joined by blank lines; `Answer.facts` = only the asked keys' facts, so C's `check_output` passes. (8) Profile for the leakage check: `core.graph.load_profile` once A merges, else `interfaces.load_profile`.
- **Contract impact:** none
- **Affects:** C: real `router.route` now exists on PR #2; the router writes every ledger entry (`local_only`, `kb_hit`, `bucket`, `blocked`) → none (C-004 already handles it). I: `mocks/cloud_cache/` is still empty, so in DEMO=1 every cloud question returns `no_data` with `sent_to_cloud=True` (the bucket is logged as sent) → please populate it (see B-005). D: E1/E2 can drive `router.route` and read `ledger.feed`/`ledger.outbound` → none.
- **Demo impact:** S4 works end to end once the cloud cache exists; S3 gets a real `local_only` ledger row.
- **Tests:** `make test` → exit 0, 269 passed; `check_network.sh` → ok; `check_ownership.py` → ok
- **Next:** queue 7 `kb.py` (exact-key store with tier + expiry, `kb.get`/`kb.put`; router already calls them), then queue 9 offline.

### B-007 · 2026-11-08 14:30 · commit `a184cf8` · PLAN v1.1

- **Change:** Added `core/kb.py` (`get`, `put`, `put_many`, `remove`, `all_facts`, `stats`, `reset`) and wired `router.route` to it, plus `tests/B/test_kb.py` (7 tests). PR #2 updated.
- **Why:** BRIEF B queue item 7. Done-when met: the same question asked twice is a `kb_hit` with 0 bytes out, and decoy keys from a sent bucket are answered from the KB too.
- **Class:** Advances
- **Plan:** advances F6, M6, P6.2, P6.5 (store all 8), I4, I6; refines M6
- **Refinements:** (1) Exact key only: no lowercasing, trimming or prefix match, so a missing key is `no_data` (I4). (2) `get(key, today=None)` never returns an expired fact. (3) Tier precedence: a `cloud` fact never replaces a `curated` fact for the same key, even one that has expired (I6). Within a tier, the most recently fetched fact wins. (4) Persistence: in memory by default; `GV_KB_PATH` → JSON file, loaded on first use and rewritten atomically on each put. (5) `stats(today)` → `{total, fresh, expired, curated, cloud}` for the UI and E2.
- **Contract impact:** none (`kb.get(key) -> Fact | None` as in CONTRACTS; the optional `today` argument is additive)
- **Affects:** C: `kb.get` is real on PR #2; `kb.stats()` is available for a "learned facts" counter. Tests that call `router.route` more than once should call `kb.reset()` in setup, or a repeat question will be a KB hit → note sent. D: E2/E4 can use `kb.reset()` for a cold KB and `GV_KB_PATH` for a warm KB that survives restarts → note sent. A: curated tables can later be loaded with `kb.put_many(Fact(tier="curated", ...))`, and cloud facts will never overwrite them → none for now.
- **Demo impact:** S6 "learns": a second ask is a 0-byte `kb_hit` in the ledger.
- **Tests:** `make test` → exit 0, 276 passed; `make check` → ownership ok, network ok
- **Next:** queue 9 offline mode (steps 1–2 only, `no_data` otherwise), then queue 8 random delays + cover buckets (G3).

### B-008 · 2026-11-08 13:55 · commit `f85b8a8` · PLAN v1.1

- **Change:** Offline mode. `core/cloud.py`: `offline()`, `set_offline(bool|None)`, `status()`; `ask_bucket` raises `CloudUnavailable` when forced offline, before demo replay. `core/router.py`: when offline, P6 steps 3–8 are skipped (no generalizing, no ledger entry, 0 bytes); KB hits and local answers still work; anything else is `no_data` with `router.OFFLINE_TEXT`. If a send fails mid-question, the remaining buckets are not tried. `core/kb.py`: `clear()` empties the store and deletes the `GV_KB_PATH` file. New `tests/B/test_offline.py` (9 tests). PR #2 updated.
- **Why:** BRIEF B queue item 9, plus D's requests (a) KB reset for cold runs and (b) an offline switch (20261108-1323-from-D-eval-needs.md).
- **Class:** Refines
- **Plan:** advances F8, M5, M6, M8, P7 E4, I8; refines F8
- **Refinements:** (1) The offline switch is `GV_OFFLINE=1`, or `cloud.set_offline(True/False)` at runtime (None goes back to the env var). (2) Forced offline wins over `DEMO=1`, so S6's offline ibuprofen beat runs in demo mode as "Wi-Fi off". (3) Offline writes no ledger entry, because nothing was decided for sending. (4) `cloud.status()` returns `{"online", "demo", "forced_offline"}` and never sends anything. `online` is False when offline is forced, when live mode has no API key, or when the last live call failed; it turns True again after the next successful call. (5) `kb.clear()` is a cold KB that also wipes the file; `kb.reset()` still just reloads from the file.
- **Contract impact:** none. `cloud.status()` is a superset of the shape in C's pending proposal (20261108-1323-C-capture-and-status-contracts.md). It is not a contract until the integrator rules on it.
- **Affects:** C: the offline badge can call `cloud.status()` if the proposal is accepted. A UI "Wi-Fi off" toggle can call `cloud.set_offline(True)`. Show `answer.text` for `no_data` as it is, because it already says "offline" → message sent. D: LiveBackend cold run = `kb.clear()`, offline = `GV_OFFLINE=1` or `cloud.set_offline(True)`. I'm not proposing a token field on `LedgerEntry` for now → message sent. A: none.
- **Demo impact:** S6 offline beat: with offline forced, the ibuprofen X5 local flags still show, and any cloud question shows the offline `no_data` text with 0 bytes.
- **Tests:** `make test` → exit 0, 285 passed; `scripts/check_network.sh` → network ok
- **Next:** queue 8: random delays and cover buckets (P6.4, P6.6), for G3.

### B-009 · 2026-11-08 14:50 · commit `bf8918b` · PLAN v1.1

- **Change:** Random delays and cover buckets. `core/cloud.py`: `pause()` sleeps a random delay (OS entropy) before every outbound request, live and demo replay; `delay_range()` reads `GV_DELAY_S=lo,hi`. `core/router.py`: `send_cover()` sends one bucket drawn uniformly from the fixed partition, without looking at any question, KB or flag. It goes through the same leakage check, writes a `cover` ledger entry (or `blocked`), and stores its 8 answers in the KB. `start_cover(interval_s=None)` / `stop_cover()` / `cover_running()` run it in a daemon thread on a steady, jittered schedule. Errors never stop the thread. Nothing is sent while offline or when the cloud is unreachable. New `tests/B/conftest.py` (no real sleeps, cover always stopped) and `tests/B/test_cover_delays.py` (14 tests). PR #2 updated.
- **Why:** BRIEF B queue item 8 (P6.4, P6.6, D-006), needed for G3. Without these, the two buckets that one question needs (e.g. Q18: b01 + b05) leave as a single tight burst, and that is what E1's joint-inference attacker exploits.
- **Class:** Advances
- **Plan:** advances P6.4, P6.6, F4, M5, M8, G3, D-006; refines P6.4/P6.6
- **Refinements:** (1) The delay is uniform in `GV_DELAY_S`, default 0.3–2.0 s before each request when live, and 0 in demo mode, where nothing leaves the device (set `GV_DELAY_S` to show it in demo). (2) The cover interval is `GV_COVER_INTERVAL_S` (default 60 s) times a random factor from 0.5 to 1.5. (3) Cover answers are stored in the KB, so cover traffic also warms the KB. (4) The app, not the router, decides when cover starts (`router.start_cover()`). Nothing starts it implicitly, so tests and evals stay deterministic.
- **Contract impact:** none. `router.route` is unchanged. The new router functions are additive inside B's module, and `cover` was already a `LedgerEntry.kind`.
- **Affects:** C: call `router.start_cover()` once at app start, and `stop_cover()` on shutdown if you like. Show `cover` rows in the ledger as "cover traffic". → message sent. D: E1 can now model cover traffic, and E3 live latency includes the delays (≈1.15 s mean per request, or set `GV_DELAY_S=0,0` to measure without them). → message sent. A: none.
- **Demo impact:** S4: the ledger can show `cover` rows between real sends if C starts cover. In demo mode there is no added latency.
- **Tests:** `make test` → exit 0, 299 passed; `scripts/check_network.sh` → network ok
- **Next:** rebalance buckets by frequency when D sends per-bucket numbers; swap to A's real X5 keys after G1; stretch: knowledge-pack sync.
