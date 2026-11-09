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

### B-010 · 2026-11-08 13:56 · commit `ad01ab4` · PLAN v1.1

- **Change:** Bulk knowledge-pack sync (BRIEF stretch). `core/router.py`: `sync_pack(skip_fresh=True, today=None) -> dict` sends every bucket of the fixed partition, in shuffled order, through the normal leakage check, logs each one as a `cover` entry (or `blocked`), and stores all answers in the KB. With `skip_fresh` it skips buckets whose 8 keys are already fresh in the KB. It returns counts (`sent`, `blocked`, `skipped`, `facts`, `offline`). Offline or unreachable cloud: nothing is sent, and the remaining buckets are not tried. New `tests/B/test_pack_sync.py` (8 tests). PR #2 updated.
- **Why:** Makes the KB warm before the user goes offline, so F8 offline questions (S6 offline ibuprofen X5) and E4's warm-KB arm get answers on-device with 0 bytes, without any query-dependent traffic.
- **Class:** Refines
- **Plan:** advances F6, F8, E4; refines P6.6
- **Refinements:** (1) Pack sync is query-independent traffic, so it is logged as `cover` (no new ledger kind, so no contract change). (2) It always covers the whole partition, the same set for every user. Only the order is random, and skipping only drops buckets that were already sent whole, so it reveals nothing new (I5). (3) It runs synchronously. The caller decides when to run it and may put it in a thread. Live: about 22 buckets × 8 requests with P6.4 delays, roughly 3 minutes. Demo: instant.
- **Contract impact:** none (additive function inside B's module; `cover` is already a `LedgerEntry.kind`).
- **Affects:** C: optional "Sync for offline" button or start-up call to `router.sync_pack()`. Show the returned counts. → message sent. D: E4 warm arm can call `kb.clear()` then `router.sync_pack()` for a fully warm KB. → message sent. A: none.
- **Demo impact:** S6 offline beat can run fully warm: sync, go offline, and the ibuprofen X5 question is a KB hit with 0 bytes. No change if unused.
- **Tests:** `make test` → exit 0, 307 passed; `check_ownership.py` → ownership ok; `scripts/check_network.sh` → network ok
- **Next:** rebalance buckets by frequency if D sends per-bucket numbers; switch to real A code after G1; otherwise support G2 merge fixes.

- **Correction to B-010:** the partition has 12 buckets, not 22. A live `sync_pack()` is 96 requests, about 2 minutes with the P6.4 delays (C/D messages said about 3 minutes, which is an overestimate).

### B-011 · 2026-11-08 14:10 · commit `f545cff` · PLAN v1.1

- **Change:** New bucket partition `data/buckets/v2.json`, now the default (`core/decoys.CURRENT_VERSION = "v2"`). It has 14 buckets and 112 keys: all 96 v1 keys plus 16 new ones. The new keys cover Alex's questions Q05, Q12/Q20 and Q14 (`CYP2C19:poor_metabolizer|citalopram`, `lisinopril|egfr<60`, `simvastatin|alt>120`) and fill the gene and lab families to multiples of 8. Keys are regrouped so each bucket holds keys of similar synthetic frequency, with these limits: at most 2 keys per co-prescription cluster per bucket (D-006), no drug twice in a gene or lab bucket, at most twice in a pair bucket, at most 2 of Alex's pairs per bucket, and omeprazole and pantoprazole in different buckets. v1 is frozen and still loads. `data/buckets/build_v2.py` records how v2 was built (one-off and offline, never run at runtime or from a query). There are 6 new tests in `tests/B/test_buckets.py`. PR #2 updated.
- **Why:** D-005 / D's 1357 message. On v1 the statistical attacker won up to 31% per bucket (one common key among rare ones). With D's synthetic priors, v2's worst bucket is 22.9% (gene 20.9%, lab 18.0%, pairs 22.9%). The 1/8 floor is 12.5%. Pair buckets can't go much lower because the pair universe is mostly rare keys.
- **Class:** Refines
- **Plan:** advances P6.5, I5, D-006, P7 E1; refines P6.5
- **Refinements:** (1) The partition is chosen by frequency balance (minimise the top-prior / bucket-total ratio) under a ≤ 2-per-cluster cap. (2) A new partition is a new version file. The old version stays loadable and unchanged; `CURRENT_VERSION` selects the live one. (3) Cloud cache replay is keyed by exact key, so it doesn't depend on the version.
- **Contract impact:** none (`Bucket`, `bucket_for`, `route` unchanged; bucket ids b01–b14 now refer to v2 content).
- **Affects:** C: the bucket members shown in the outbound view change (Alex's clopidogrel|omeprazole is now in b13, not b05). Nothing to change if you read from the ledger/decoys. → message sent. D: rerun E1 on v2. Four new lab keys have no prior yet (`lithium|egfr`, `atorvastatin|alt`, `valproate|alt`, `methotrexate|egfr`; I used 3 and the clusters bipolar, diabetes_ckd, epilepsy, rheumatoid). Q05/Q12/Q14/Q20 keys are now sendable. → message sent. A: please confirm `simvastatin|alt>120` and `lisinopril|egfr<60` match your band spelling. → message sent.
- **Demo impact:** S4: different decoy texts next to the real question in the ledger. S5: red-team chart should show a lower statistical-attacker bar once D reruns.
- **Tests:** `make test` → exit 0, 344 passed; `check_ownership.py --range origin/main..HEAD` → ownership ok; `scripts/check_network.sh` → network ok
- **Next:** adjust v2 key spellings if A replies before G2 (v2 freezes at G2); switch to real A code after G1; G2 merge fixes.

### B-012 · 2026-11-08 14:08 · commit `a951d58` · PLAN v1.1

- **Change:** New bucket partition `data/buckets/v3.json`, now the default (`core/decoys.CURRENT_VERSION = "v3"`). It has 17 buckets and 136 keys: all 112 v2 keys, the 15 keys A's real rule tables can emit that v2 lacked, and 9 decoy keys that fill the gene and pair families to multiples of 8. The 15 are `CYP2C19:intermediate_metabolizer|clopidogrel`, `SLCO1B1:poor_function|simvastatin`, `clopidogrel|esomeprazole`, and the NSAID × antiplatelet/ACE class expansions (naproxen, celecoxib, prasugrel, ticagrelor pairs). The decoys are 6 gene keys (metoprolol, paroxetine, ondansetron, celecoxib, ibuprofen, rosuvastatin) and 3 warfarin pairs (celecoxib, ibuprofen, naproxen). It uses the same frequency-balanced method and limits as v2. v1 and v2 are frozen and still load. `build_v2.py` was refactored so `build_v3.py` can reuse it; v2 regenerates byte-identical. New tests: v3 covers all 24 keys from A's `rules.all_keys()`, plus a guard that runs once `core/rules.py` is on main and fails if any rule key falls outside the universe.
- **Why:** A-003 / A's 13:59 message. A key outside the universe can never be sent (I4/I5 → `no_data`). So the needs_cloud flag `CYP2C19:intermediate_metabolizer|clopidogrel` could never get a cloud answer, and D's Q17 (`in_universe: true` for the naproxen keys) did not hold on v2. Worst-bucket statistical attacker with D's synthetic priors: 22.2% (gene 20.0%, lab 18.0%, pairs 22.2%), down from v2's 22.9%.
- **Class:** Refines
- **Plan:** advances P6.5, I4, I5, D-006, P7 E1, G2; refines P6.5
- **Refinements:** (1) The bucket universe must contain every exact key the local rule tables can emit. A test enforces this against `rules.all_keys()`. (2) New topics D's fixture has no cluster for: newer P2Y12 + NSAID pairs get their own cluster `acs_nsaid`, NSAID + aspirin/ACE/clopidogrel-naproxen pairs go in `chronic_pain`, and NSAID + warfarin pairs go in `anticoagulation`.
- **Contract impact:** none (`Bucket`, `bucket_for`, `route` unchanged; bucket ids are now b01–b17 and point at v3 members).
- **Affects:** C: bucket ids and members in the outbound view change again (Alex's `clopidogrel|omeprazole` is in b14). Nothing to change if you read from the ledger/decoys; don't hard-code 14 buckets → message sent. D: rerun E1 on v3. Q17's three naproxen keys are now in the universe. `clopidogrel|esomeprazole` is in (b13), so don't use it as an out-of-universe example; `clopidogrel|st_johns_wort` (Q16) is still out. Nine new topics use DEFAULT_PRIOR 3 → message sent. A: nothing required. If you add rule keys later, the B guard test fails until I add them to a new version → message sent.
- **Demo impact:** S4: different decoy texts next to the real question. S5: the statistical-attacker bar drops slightly once D reruns. S6: omeprazole and pantoprazole pairs are still in different buckets (b14 / b15).
- **Tests:** `make test` → exit 0, 394 passed; `check_ownership.py --range origin/main..HEAD` → ownership ok
- **Next:** switch to real A code after G1 (graph.load_profile, rules); G2 merge fixes; keep v3 frozen from G2.

### B-013 · 2026-11-08 14:15 · commit `d5d16bc` · PLAN v1.1

- **Change:** (1) New `validator.wording_problems` / `check_wording` (I7). Every cloud answer, live or replayed from `mocks/cloud_cache/`, goes through it in `cloud.ask_bucket`. An answer that contains any word with "safe" in it (safe, safely, safety, unsafe), or that tells the reader to start, stop or change a medicine, is dropped. Instructions are caught as sentence-initial imperatives ("Stop taking…", "Do not take…", "Avoid…") or "you should/must/need to/can/may want to" + verb. Descriptive phrasing like "Use of…", "Increase in…" or "patients who stop taking…" still passes. A dropped answer's key reads as `no_data`. (2) `python -m core.cloud record <dir>` can now be restarted: it skips buckets whose file already has every key. It also writes the raw answers, so the check below can show what will be dropped. (3) New `python -m core.cloud check [<dir>]` / `cloud.check_cache()`. It is offline-only and lists the partition keys with no answer, I7-rejected answers with the reason, and cached keys outside the partition. It exits 0 only if all 136 keys are usable.
- **Why:** Nothing enforced I7 on cloud text. The system prompt only asks the model to avoid "safe", and the router passes fact text straight into `Answer.text`, so a live or recorded answer saying "generally safe" would reach the UI. D-006: S4/S6 are blocked on an empty demo cache. A full record makes 136 live calls, so it must survive a mid-run failure and be verifiable before rehearsal.
- **Class:** Advances
- **Plan:** advances I7, I8, I4, M8, P6.5; unblocks D-006 (S4/S6 cache)
- **Contract impact:** none (`ask_bucket` signature unchanged; new functions are additive inside B's modules)
- **Affects:** I: record the demo cache with `ANTHROPIC_API_KEY=… python -m core.cloud record mocks/cloud_cache`, then run `python -m core.cloud check` and re-record or hand-edit any rejected key → message sent. C: an answer that used to show text may now be `no_data`; nothing to change → message sent. D: router output now satisfies I7 by construction, so an E-check for "safe" in answers should pass; `check_cache` can feed a demo-readiness check → message sent.
- **Demo impact:** S4/S6 can be rehearsed once the cache is recorded and `check` exits 0. No answer on screen can say "safe".
- **Tests:** `make test` → exit 0, 415 passed (21 new in `tests/B/test_wording.py`); `check_ownership.py --range origin/main..HEAD` → ownership ok. `python -m core.cloud check` on today's empty cache → 0/136 usable, exit 1 (expected).
- **Next:** switch to real A code after G1; G2 merge fixes; rebuild v3 only if D's priors arrive before G2.

### B-014 · 2026-11-08 14:18 · commit `800a75f` · PLAN v1.2

- **Change:** New bucket partition `data/buckets/v4.json`, now the default (`core/decoys.CURRENT_VERSION = "v4"`). Still 17 buckets and 136 keys. The 7 CYP2D6 decoy keys from v3 are swapped for 7 keys on SNP-callable genes: `CYP2C19:poor_metabolizer|amitriptyline`, `CYP2C19:poor_metabolizer|escitalopram`, `CYP2C19:poor_metabolizer|voriconazole`, `CYP2C9:poor_metabolizer|meloxicam`, `HLA-A:3101_positive|carbamazepine`, `SLCO1B1:poor_function|atorvastatin`, `TPMT:poor_metabolizer|mercaptopurine`. Only the 4 gene buckets (b01–b04) are regrouped; the 13 lab and pair buckets (b05–b17) are copied from v3 unchanged. v1–v3 are frozen and still load. `build_v4.py` reuses v2's method; `build_v2.partition` now skips an empty family (v2/v3 output is unchanged). The cloud.status() task (D-020, queue 9) was already implemented and tested in B-010 (`{online, demo, forced_offline}`, sends nothing).
- **Why:** D-021 / PLAN v1.2 P5 makes CYP2D6 `not_assessed` for every user. The code is public, so an observer knows a CYP2D6 key can never be a real query, and every CYP2D6 bucket member is a known decoy. In v3 that cut the effective k to 4 in b04 (4 CYP2D6 keys) and to 6–7 in b01–b03, which breaks I5 (k = 8). The cache is still empty, so this is the cheapest moment to change the gene buckets. Worst gene bucket for the statistical attacker (D's synthetic priors @ f69dc14): 22.2%.
- **Class:** Refines
- **Plan:** advances I5, P6.5, D-021; refines D-003 (partition version)
- **Refinements:** A decoy key must be a topic the app could really query for some user. Genes PLAN marks `not_assessed` (today: CYP2D6) are excluded from the partition. No pantoprazole gene key sits in a bucket with the omeprazole gene key (S6 no-extrapolation, test enforced).
- **Contract impact:** none (`Bucket`, `bucket_for`, `route` unchanged; ids b01–b17 unchanged; only b01–b04 members change)
- **Affects:** D: gene bucket members b01–b04 changed; lab/pair buckets identical to v3; rerun E1 gene numbers on v4; don't use CYP2D6 keys as in-universe examples → message sent. I: record `mocks/cloud_cache` against v4 (the default); B has no API key, so option (b) → message sent + to-human (§9, secret needed). C: nothing to change (outbound view reads buckets from decoys/ledger) → none. A: nothing required; if your rules still emit a CYP2D6 key, the B guard test fails, which D-021 intends → none.
- **Demo impact:** S4: different decoy texts next to the gene questions. S6: unchanged (omeprazole/pantoprazole pairs still b14 / b15).
- **Tests:** `make test` → exit 0, 450 passed (3 new in `tests/B/test_buckets.py`); `check_ownership.py --range origin/main..HEAD` → ownership ok
- **Next:** switch to real A code after G1 (graph.load_profile, rules); G2 merge fixes; keep v4 frozen from G2.

### B-015 · 2026-11-08 14:26 · commit `5f0144a` · PLAN v1.2

- **Change:** New partition `data/buckets/v5.json`, now the default (`core/decoys.CURRENT_VERSION = "v5"`). It keeps 17 buckets of 8 member keys (136), and the file gets a new top-level `aliases` map with 4 entries: `CYP2C19:intermediate_metabolizer|clopidogrel` → `CYP2C19:poor_metabolizer|clopidogrel`, `SLCO1B1:poor_function|simvastatin` → `SLCO1B1:decreased_function|simvastatin|dose>20mg`, `CYP2C19:ultrarapid_metabolizer|escitalopram` → `CYP2C19:poor_metabolizer|escitalopram`, `SLCO1B1:decreased_function|atorvastatin` → `SLCO1B1:poor_function|atorvastatin`. New `decoys.load_aliases`, `canonical` and `aliases_of`. `bucket_for(alias)` returns the member's bucket. `universe()` still lists members only. `router._send_bucket` stores each member's answer under its alias keys too, so `route` and `sync_pack` fill the aliases (`sync_pack` now reports `facts` = 136 + 4). The 4 freed gene slots hold decoys on SNP-callable genes: `CYP2C9:poor_metabolizer|piroxicam`, `DPYD:poor_metabolizer|capecitabine`, `TPMT:poor_metabolizer|thioguanine`, `UGT1A1:poor_metabolizer|atazanavir`. Only the gene buckets b01–b04 are regrouped; b05–b17 are identical to v4. v1–v4 are frozen and still load. `build_v5.py` documents the build. I also removed 4 stray untracked " 2" duplicate files from the code worktree again (byte-identical copies).
- **Why:** D's E1 finding (20261108-1415-from-D-v3-results §3). Variants of one generalized topic sat in different buckets, and the outbound text is identical for both variants. So the bucket that leaves depended on the phenotype: guess the topic and you also learn the genotype (I3). Alex's two gene topics were affected. v4 had 4 such splits; v5 has none. I took D's option 2, "bucket by the generalized topic and store under every variant's key", rather than option 1, putting variants in one bucket. Option 1 would put two identical texts in one bucket, which leaves 7 distinct topics (lower effective k, I5) and breaks the one-drug-per-gene-bucket rule. Worst gene bucket for the statistical attacker is 21.1% (v4: 22.2%).
- **Class:** Refines
- **Plan:** advances I3, I5, P6.5; refines D-003 (partition version), P6.4 (one outbound text per generalized topic)
- **Refinements:** (1) A partition file may carry `aliases`, which map a variant key to the member key of the same generalized topic (gene + drug, ignoring phenotype and dose band). An alias is never a bucket member. It resolves to the member's bucket and gets the member's answer, and nothing extra is sent. (2) Every bucket's 8 texts are 8 distinct topics, and no generalized topic resolves to two buckets (both test-enforced). (3) The member of a variant group is the dosed variant if there is one, otherwise the `poor_*` variant.
- **Contract impact:** none. `Bucket` still holds 8 distinct keys; `bucket_for`, `universe`, `route` and `sync_pack` signatures are unchanged; `aliases` is additive in a B-owned data file.
- **Affects:** D: rerun E1 on v5. Your `generalized_view` reads only `keys`, so it now sees one member per topic and `view_key` of a variant falls back to its generalized key in the right bucket. `splits` should come out empty (message sent). I: the demo cache must be recorded against v5, not v4. Cache files are keyed by member keys (136), and `cloud check` counts members only. The API-key escalation still stands (message sent). A: nothing to do. `rules.all_keys()` keys all resolve through `bucket_for` (test enforced). C: nothing. The outbound view still shows 8 texts per bucket; a fact's `key` is the exact key that was asked about.
- **Demo impact:** S4: different decoy texts in the gene buckets; CYP2C19+clopidogrel and SLCO1B1+simvastatin now leave in the same bucket (b03), one send for both of Alex's gene questions. S6 is unchanged (omeprazole/pantoprazole pairs still b14 / b15; no pantoprazole gene key).
- **Tests:** `make test` exit 0, 424 passed (5 new: 4 in `tests/B/test_buckets.py`, 1 in `tests/B/test_router.py`; 1 updated in `test_pack_sync.py`). B-014's 450 included the stray duplicate test files I have now removed. `check_ownership.py --range origin/main..HEAD` → ownership ok. I did not run a merged run with A/C/D branches this cycle.
- **Next:** merged run with A/C/D branches to check D's `splits` is empty on v5; switch to real A code after G1; freeze v5 from G2.

### B-016 · 2026-11-08 14:40 · commit `85ab929` · PLAN v1.2

- **Change:** `core/validator.wording_problems` (I7 filter on every cloud answer, live or replayed) now normalizes text before checking it: NFKC, Unicode format characters (zero-width, soft hyphen) dropped, Cyrillic/Greek look-alikes mapped to Latin, and spelled-out runs of 3+ single letters ("s a f e", "S.A.F.E.") joined. It then rejects: (1) any word containing "safe" (unchanged); (2) reassurance without the word: fine, harmless, no risk, risk-free, without risk, nothing to worry/fear, no concern, not a problem, okay/alright to, won't hurt; (3) non-English answers (mostly non-Latin script, or 2+ common es/fr/de/pt/it function words outnumbering English ones); (4) instructions: an imperative at sentence start with more verbs (consider, try, keep, hold, pause, cut, add, drop, substitute, replace, taper, wean, go ahead), a subject + modal + such a verb anywhere ("Patients should stop", "You could switch", "You'll want to stop", "Patients can keep"), or advice phrasing ("it is best to", "I would recommend", "... is recommended/advisable/advised", "should be stopped"). "Take-home message" no longer reads as an imperative. D's 35 red-team texts plus 3 more (Cyrillic sentence, full-width "ｓａｆｅ", "µg") are now B tests.
- **Why:** D's red team (20261108-1426-from-D-wording-latency-v4 §1, D-008): B-013 caught 3 of 25 attacks and raised 1 false alarm. Now it catches 25/25 with 0 false alarms on D's 8 neutral texts. These are hand-written attacks, not measured cloud output, so this closes known gaps; it does not prove a rate.
- **Class:** Refines
- **Plan:** advances I7, P6.5; refines the I7 filter rules (stricter; a rejected answer reads as `no_data`, I4)
- **Refinements:** The I7 filter checks the normalized text (NFKC, no invisible characters, look-alikes mapped) and rejects reassurance synonyms, non-English answers, and advice in any grammatical form (imperative, subject+modal, "is recommended"), not just "safe" and sentence-start imperatives.
- **Contract impact:** none (`wording_problems`/`check_wording` signatures unchanged)
- **Affects:** D: re-run `python -m eval.wording` on a merge (expect 25/25, 0 false alarms) → message sent. I: the stricter filter may reject more recorded cache answers; `python -m core.cloud check` lists them under `rejected` → no new action. C: nothing (rejected answers already read as `no_data`). A: nothing. The current `mocks/cloud_cache` has 0 answers rejected by the new filter.
- **Demo impact:** none on scripted beats. A cloud answer that reassures or advises now shows as `no_data` (S5/S6 wording stays I7-clean).
- **Tests:** `make test` exit 0, 512 passed (38 new in `tests/B/test_wording.py`); `check_ownership.py --range origin/main..HEAD` → ownership ok.
- **Delay cost (D §2, P6.4):** I'm keeping the sequential per-request pauses for now. Sending a bucket's 8 requests at once cuts live latency about 8× but makes the 8 requests land together, which weakens the timing cover. Demo mode is unaffected. I'll ask the integrator if live latency becomes a demo issue.
- **Next:** merged run with A/C/D branches (D's `splits` empty on v5, wording 25/25); switch to real A code after G1; freeze v5 from G2.

### B-017 · 2026-11-08 14:50 · commit `b960699` · PLAN v1.2.1

- **Change:** New `tests/B/test_g2_real_rules.py` (5 tests; tests only, no code change). It runs the G2 path on A's real code from main (D-022) with no mock profile or flags: `graph.load_profile()` → `rules.check_all()` → `router.route()` → ledger. Only the cloud is replayed (DEMO=1), from a temporary cache that answers every partition key. The tests check five things. (1) The real engine fires X1–X4, and every flag that needs the cloud has a bucket: X1 `CYP2C19:poor_metabolizer|clopidogrel` and X2 `clopidogrel|omeprazole`. (2) One question answers both and sends exactly their two buckets (b03, b14). Each bucket sends 8 distinct texts with `bytes_out > 0` and `personal_fields_sent == 0`, passes `check_outbound` against the real profile, and contains no genotype string. The answer passes `check_output` (I4) and the I7 wording filter. (3) Asking again gives a single `kb_hit` with 0 bytes. (4) X3/X4 on their own are `local_only`. (5) Offline, ibuprofen fires X5 locally and 0 bytes leave (S6, F8).
- **Why:** G2 needs "one question end to end with live ledger". Until now B's router tests used hand-written flags and the mock profile. These tests show the G2 path works on the real merged engine, so B's side of G2 can be checked on main and not only in a throwaway merge.
- **Class:** Advances
- **Plan:** advances G2, P6 (steps 1–5, 7, 8), I3, I4, I5, I7, F8; D-022
- **Contract impact:** none
- **Affects:** none, so no messages. A: if a rule change stops X1/X2 needing the cloud, or adds a cloud key with no bucket, these tests fail (the existing guard test already catches the second case). C, D: nothing.
- **Demo impact:** none. S4's two sends (b03, b14) are now covered by tests on real flags.
- **Tests:** `make test` exit 0, 1048 passed. That count includes the untracked " 2"/" 3" duplicate test files that Desktop sync keeps recreating; without them it is 609 passed. `check_ownership.py --range origin/main..HEAD` → ownership ok.
- **Next:** G2 merge of PR #2. A's no_data helper (A queue 8) is not on main and A's loop is stopped, so that item stays blocked. The demo cache still needs an API key (to-human 1418).

### B-018 · 2026-11-08 14:45 · commit `cafebe3` · PLAN v1.2.1

- **Change:** `router.route()` no longer answers `known` ("checked on your device, nothing sent") when no flag covers the question. The question is still read only on the device, and three kinds of exact key now come from it: (1) pairs of named drugs, as before; (2) gene-drug keys in the partition (or its aliases) for a named drug, when the question mentions genes and the gene is assessed in the profile; (3) drug-lab keys in the partition when the question names a lab test (CK, liver/ALT, kidney/eGFR, potassium, INR, ...), for the named drugs, or for the drugs in the caller's flags when the question names none. A gene or lab key is skipped when a flag already covers that gene or lab for that drug. A local flag "covers" the question if it shares a drug the question names, or if the question names no drug. The answer is `known` only when it has facts, or when a flag covers the question and no key that the cloud or the partition could answer is left open. Everything else is `no_data`, with `NO_DATA_TEXT`, or `OFFLINE_TEXT` when offline. 7 new tests in `tests/B/test_router.py`.
- **Why:** D reported an I4 break (inbox 20261108-1438). With no flag, Q16 St. John's wort, Q03 codeine and Q04/Q05 warfarin/citalopram came back as "checked, nothing found", and Q04/Q05 never reached the cloud. Offline Q13/Q14 (CK/ALT with X3 only) also read as `known`.
- **Class:** Advances (I4: missing = `no_data`)
- **Plan:** advances I4, P6.1–P6.3, E4; refines P6.1
- **Refinements:** P6.1 "local rules answer it" applies only when a flag covers the question (it shares a named drug, or the question names none) and no answerable key is left open. The router reads the question's own subject locally: named pairs, plus gene-drug keys when it says "genes", plus drug-lab keys when it names a lab. Asked keys outside the partition are never sent and do not, on their own, hold back an answer that a covering flag gives (Q17 naproxen class rule stays `known`, online and offline).
- **Contract impact:** none. `route(question, flags) -> Answer` is unchanged.
- **Affects:** C: more questions now come back as `no_data`, and the text is the existing `NO_DATA_TEXT`/`OFFLINE_TEXT`. A gene question with no flag (Q04 "would my genes matter if I needed warfarin?") now sends its buckets (b01 + b03) → C: no code change, but the ledger shows those sends. D: I4 check now passes → re-run on the merge. A: none. `rules.no_data_keys` is not needed for this.
- **Demo impact:** none on the scripted beats. S3 X1–X4 and S6 pantoprazole/offline ibuprofen behave as before. An off-script gene question now goes to the cloud as buckets and is no longer a false "checked locally".
- **Tests:** `make test` exit 0, 1055 passed (7 new; the count includes the untracked " 2"/" 3" duplicates). Temporary merge of B + origin/D + C + A: `python -m eval.offline` gave matches_offline_state_cold 20/20 and `unbacked_known: []`. `python -m eval.gate` gave I4 PASS (14 pass, 3 warn, 0 fail). The warns are D's fixture partition, the simulated E2, and the I7a skip. With DEMO replay from a cache that answers every bucket, all 20 queries return their `expected_state` online. `check_ownership.py` → ownership ok.
- **Next:** G2 merge of PR #2. The demo cache still needs the API key (to-human 1418). Stretch: pack sync polish.

### B-019 · 2026-11-08 14:49 · commit `6b81173` · PLAN v1.2.1

- **Change:** `router._named_drugs` now also reads A's `normalize.to_ingredients` (G1 contract), limited to the bucket universe, so a brand name in the question counts as its ingredient. "Is Plavix OK with Protonix?" now asks `clopidogrel|pantoprazole`, and "Advil with my lisinopril" asks `ibuprofen|lisinopril`. If the normalizer raises, the old word match is used alone.
- **Why:** The router matched only bare ingredient words. A brand-name question named no drug, so the demo pair key was never looked up. With a local clopidogrel flag (e.g. X2) the answer came back `known` ("checked on your device"), which breaks I4. C passes the raw question to `route`, so the fix belongs here.
- **Class:** Advances
- **Plan:** advances F4, I4, P6.1
- **Contract impact:** none (`route` unchanged; uses `normalize.to_ingredients`)
- **Affects:** C: brand-name questions now route by exact key and may send a bucket. No code change needed. D: you could add a brand-name query (e.g. "Plavix with Protonix") to the E4/I4 set. A: none. Multi-word ids (`st_johns_wort`) are now readable too, but none are in v5.
- **Demo impact:** S6 works whether the pantoprazole question is typed with brand names or ingredient names. Nothing else changes.
- **Tests:** `make test` exit 0, 1058 passed (3 new in `tests/B/test_router.py`; all 3 fail without the fix). Caught up on D-023/D-024 (no code impact), A-008 and to-B 1444 (no new bucket drugs, no change needed).
- **Next:** G2 merge of PR #2; demo cache once the API key is available (to-human 1418).

### B-020 · 2026-11-08 15:00 · commit `425f764` · PLAN v1.2.1

- **Change:** `tests/B/conftest.py` sets `collect_ignore_glob = ["* [0-9].py", "* [0-9][0-9].py"]`, so pytest skips the untracked macOS Finder copies ("test_cloud 3.py" etc.) in `tests/B/`.
- **Why:** Those copies are never committed, but locally pytest collected 439 extra tests from them, so the local count (1058) did not match CI and a stale copy could go red for no real reason. Real B+repo count is 619.
- **Class:** Refines
- **Plan:** none directly (test hygiene for B's scope ahead of G2)
- **Refinements:** B's local test runs ignore Finder duplicate files named "* N.py".
- **Contract impact:** none
- **Affects:** none. Other agents' worktrees can have the same Finder copies; this only covers `tests/B/`.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 619 passed. Rebased on main (only coord commits since B-019), PR #2 CI green. No new inbox messages, DECISIONS (D-024) or LOG entries since last cycle.
- **Next:** G2 merge of PR #2; demo cache once the API key is available (to-human 1418). Queue 1–9 done; stretch (knowledge-pack sync) next if G2 is still pending.

### B-021 · 2026-11-08 15:10 · commit `8e98cf1` · PLAN v1.2.1

- **Change:** No code change. Rebased PR #2 on main 7aad6b0 and force-pushed it (head 8e98cf1). Rewrote the PR #2 title and body as a G2 review guide. The old body described only queue 1 (v1 buckets, 14 tests). The new one maps every file to its queue item and PLAN IDs, lists the checks, and names the one open item.
- **Why:** PR #2 is the G2 merge. With a 4640-line diff and a stale description, the integrator could not review it quickly.
- **Class:** Advances
- **Plan:** advances G2 readiness (F4, M5, P6, I3, I4, I5, I7, all already in the code)
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I (integrator): PR #2 is ready for G2 review, and the guide is in the PR body. A, C, D: none. A-010 (genotype sweep, tests only) does not affect B.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 619 passed. `check_ownership.py --range origin/main..HEAD` ok. I2 network grep over tracked files is clean. Locally, `check_network.sh` flags the untracked Finder copies `core/cloud 2.py` and `core/cloud 3.py`. They are not in git, so CI does not see them. I have not deleted them.
- **Next:** G2 merge of PR #2, then freeze bucket v5. Record the demo cache once the API key arrives (to-human 1418). Until then, take requests from A, C and D.

### B-022 · 2026-11-08 14:59 · commit `30becd4` · PLAN v1.2.1

- **Change:** No code change. Rebased PR #2 on main c51bb43 (only coord commits since 7aad6b0) and force-pushed it (head 30becd4).
- **Why:** Keep the G2 PR on current main.
- **Class:** Advances
- **Plan:** G2 readiness only
- **Refinements:** none
- **Contract impact:** none
- **Affects:** none. C-018 (palette hexes, D's screenshots) does not touch B. No new inbox messages, DECISIONS (still D-024), proposals for B or PLAN bump (still v1.2.1).
- **Demo impact:** none
- **Tests:** `make test` exit 0, 619 passed. PR #2 CI green before this push; mergeable.
- **Next:** G2 merge of PR #2, then freeze bucket v5. Record the demo cache once the API key arrives (to-human 1418; `python -m core.cloud record` then `check`).
- **Note:** the B-021 header time (15:10) was ahead of the system clock; this entry uses the system clock.

### B-023 · 2026-11-08 15:02 · commit `20000fc` · PLAN v1.2.1

- **Change:** Tests only. I merged main + A's PR #5 (`143fa41`) + B's PR #2 in a scratch worktree before G2, and 1 test failed: `tests/B/test_buckets.py::test_rule_keys_match_real_rules_when_present`. A's new allergy table adds `allergy:<group>|drug` keys to `rules.all_keys()`, and the test required every rule key to sit in a bucket. Allergy flags never go to the cloud (`generalize` returns `[]`, B-002 refinement 6), so these keys belong outside the universe. The test now leaves `allergy:` keys out and also asserts that none of them is in a bucket. New test `test_allergy_flag_never_leaves_the_device` (tests/B/test_g2_real_rules.py) runs Alex's real penicillin allergy against amoxicillin, forces `needs_cloud=True`, and routes the flag. It must come back `local_only` with 0 bytes and 0 personal fields. It skips until PR #5 merges.
- **Why:** PRs #2 and #5 must merge in either order without turning main red at G2. The router and buckets were already right. Only the test's assumption was wrong.
- **Class:** Advances
- **Plan:** advances F3 (allergy), I3, G2
- **Refinements:** none (B-002 refinement 6 already covers it, and the tests now enforce it)
- **Contract impact:** none
- **Affects:** A: PR #5 merges green with PR #2. Keep the `allergy:` prefix on allergy keys, because the tests key off it → nothing to do. I: G2 can merge #2 and #5 in either order → none. C, D: none. C-019 (white accent, visual only) does not touch B.
- **Demo impact:** none. Bucket v5 is unchanged.
- **Tests:** B branch: `make test` exit 0, 619 passed, 1 skipped (the new allergy test, waiting on PR #5). main + PR #5 + PR #2 (`20000fc`): `make test` exit 0, 713 passed, 0 skipped (the allergy test runs and passes).
- **Next:** G2 merge of PR #2, then freeze bucket v5. Record the demo cache once the API key arrives (to-human 1418).

### B-024 · 2026-11-08 15:05 · commit `9743eed` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** `core/cloud.py` live requests now send `"thinking": {"type": "between_tools"}` and `max_tokens` 1000 (was 400). A reply with no text (e.g. only an empty thinking block, `stop_reason: max_tokens`) still reads as `no_data` (I4), but `cloud` now logs a warning naming the bucket key and stop_reason instead of dropping it silently. The log carries only the generalized key, nothing about the user. SYSTEM_PROMPT gains the integrator's neutral-reporting sentence ("Write in neutral reporting style ... Never write is recommended, are advised, is preferred, should ..."), so live answers match how the knowledge pack was recorded. The I7 filter is unchanged, not loosened. 3 new tests in `tests/B/test_cloud.py`.
- **Why:** Integrator message 20261108-1501 / D-026 (G2 blocker), in PR #6 and not yet on main: about 25% of live answers came back empty because the model spent its 400 tokens thinking.
- **Class:** Advances
- **Plan:** advances D-026, F4, M8; keeps I4, I7; matches D-027 pack prompt
- **Refinements:** the off switch lives in one constant, `cloud.THINKING`
- **Contract impact:** none (`ask_bucket`/`status` signatures unchanged)
- **Affects:** D: live E2 runs should stop losing answers to empty replies, so expect fewer `no_data` in live mode. Nothing to do. I: PR #2 head is now `9743eed`, which carries D-026 for G2. Demo replay and `check` do not use the request body, so the pack is unaffected. A, C: none.
- **Demo impact:** none in DEMO=1 (replay). Live mode answers more reliably.
- **Tests:** `make test` exit 0, 622 passed, 1 skipped (allergy test, waits on PR #5).
- **Next:** G2 merge of PR #2, then rebase onto v1.3 once PR #6 merges. Then take D-027 work: `router.sync_pack()` vs the committed pack, and the bucket v5 freeze.

### B-025 · 2026-11-08 15:10 · commit `1cc90f8` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** `router.route()` now looks up a `needs_cloud` flag's key only when that flag covers the question. A flag covers it when it shares a drug the question names, or when the question names no drug at all. This is the rule `flag_covers` already used to decide `known`. Before, every cloud flag passed in went into the lookup whatever the question asked. 3 new tests in `tests/B/test_router.py`.
- **Why:** I checked PR #6's knowledge pack (D-027) against this branch (pack read from `origin/integrator/v1.3` into a temp dir, DEMO=1). `cloud check` gives 136/136 ok, 0 missing, 0 rejected, 0 unknown. `sync_pack(skip_fresh=False)` sent 17 buckets and stored 140 facts (136 keys + 4 v5 aliases). A second `sync_pack()` skipped all 17. Synced questions are `kb_hit` with 0 bytes and still answer with GV_OFFLINE. But with Alex's real `check_all` flags, "Is simvastatin affected by my genes?" and "Can I take ibuprofen?" both came back `known` using the clopidogrel X1/X2 cloud texts. That breaks I4 (an answer must be backed by facts about what was asked). Without a pack sync, the same questions sent the clopidogrel buckets for no reason.
- **Class:** Refines
- **Plan:** advances F4, F6/D-027 (pack check); refines P6.1/P6.2 and I4
- **Refinements:** P6.1: a question looks up only the flags that cover it (they share a named drug, or the question names no drug). Off-topic flags are neither sent nor quoted.
- **Contract impact:** none (`route(question, flags) -> Answer` unchanged)
- **Affects:** C: `/api/ask` passes all med flags. An off-topic question (e.g. ibuprofen, not a med) now gets `no_data`, not clopidogrel text. If you want such a question answered locally, also pass `rules.check(Drug(<named drug>), profile)` flags for the drugs it names. Optional. D: E1/E4 question sets already pass per-question flags, so little should change. Questions with no `drugs` that use `check_all` will no longer pull X1/X2 when their text names another drug. Rerun once. I: the D-027 pack works with PR #2 as-is, so PR #6 + PR #2 merge cleanly from B's side. A: none.
- **Demo impact:** S4/S5: questions about clopidogrel are unchanged. Off-topic questions stop quoting clopidogrel text. Fewer buckets leave in live/cold mode.
- **Tests:** `make test` exit 0, 625 passed, 1 skipped (allergy test, waits on PR #5).
- **Next:** G2 merge of PR #2. After PR #6 merges, rebase onto v1.3 and add a test that runs `sync_pack` against the committed `mocks/cloud_cache/`. v5 stays frozen (D-027).

### B-026 · 2026-11-08 15:20 · commit `170ba35` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** `router.route()` now puts the exact drug-drug pair the question names (`_question_keys`) first in `Answer.facts` and `Answer.text`. The other keys (covering flags, then gene/lab subject keys) follow in the same order as before. Only the order changed: the same keys are looked up and the same buckets are sent. 2 new tests in `tests/B/test_router.py`.
- **Why:** C's suggestion (20261108-1510). On Q07, "Can I take pantoprazole with clopidogrel instead?", the facts came back as X1 `CYP2C19:poor_metabolizer|clopidogrel` first, then `clopidogrel|omeprazole`, then `clopidogrel|pantoprazole`. So the pair the user asked about was 7th of 9 paragraphs.
- **Class:** Refines
- **Plan:** advances F6, S3/S4 (answer readability); refines P6 answer composition
- **Refinements:** P6: `Answer.facts` order is (1) the pairs the question names, (2) covering flags' keys, (3) the other subject keys. The order never changes what is sent.
- **Contract impact:** none (`Answer` unchanged)
- **Affects:** C: when the question names a pair the partition covers, `facts[0]` is that pair. You can lead with it without re-sorting in merge (re-sorting is still harmless). D: none (E-checks look at keys and bytes, not order). A, I: none.
- **Demo impact:** S4: the Q07 answer starts with pantoprazole + clopidogrel.
- **Tests:** `make test` exit 0, 627 passed, 1 skipped. The new leading-pair test fails on the old order.
- **Next:** G2 merge of PR #2. After PR #6 merges, rebase onto v1.3 and add a `sync_pack` test against the committed `mocks/cloud_cache/`.

### B-027 · 2026-11-08 15:35 · commit `f6d6ae0` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** New `tests/B/test_committed_pack.py` (3 tests) for the committed knowledge pack in `mocks/cloud_cache/` (D-027): (1) one file per v5 bucket, each holding exactly that bucket's 8 keys; (2) every recorded answer is non-empty and passes `wording_problems` (I7); (3) `router.sync_pack()` in `DEMO=1` against the real pack sends all 17 buckets as cover, blocks none, and stores 136 facts plus the alias copies, with 0 personal fields. The tests skip while the pack isn't on the branch. `GV_PACK_CHECK=<dir>` points them at another pack.
- **Why:** The pack is frozen with partition v5 (D-027). If someone changes v5 or re-records part of the pack, this test catches the mismatch before the demo replays half a pack or a reply that breaks I7.
- **Class:** Advances
- **Plan:** advances F6, F8, I7, E4; stretch pack sync
- **Contract impact:** none
- **Affects:** none. I: once PR #6 merges, these 3 tests stop skipping on main. I checked them against PR #6's pack (copied from `origin/integrator/v1.3` into a temporary folder, deleted afterwards): 3 passed.
- **Demo impact:** none (S6 sync is protected by a test now)
- **Tests:** `make test` exit 0, 627 passed, 4 skipped (the 3 new tests skip without the pack). With the PR #6 pack: 3 passed.
- **Inbox:** nothing new. Read A-013 (capture: only the label's first drug line counts): no effect on B.
- **Next:** G2 merge of PR #2. After PR #6 merges, rebase onto v1.3 and confirm the 3 tests run, not skip.

### B-028 · 2026-11-08 15:45 · commit `cb4a705` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** New `tests/B/test_combo_questions.py` (5 tests). These cover questions that name a combination product, the way A-014 now reads one ("ezetimibe-simvastatin 10-40 mg", "amox-clav"). The tests use a stand-in for A's `to_ingredients` until PR #5 merges. They check that: (1) only universe ingredients count as named, so the combo question asks `clopidogrel|simvastatin` and nothing about ezetimibe; (2) online, no outbound text has "ezetimibe", "10-40" or the question, and 0 personal fields are sent; (3) offline, the answer is `no_data` with nothing sent; (4) amox-clav with the AL-001 allergy flag stays `local_only` with 0 bytes; (5) "clavulanate" never leaves the device. No router code changed: all 5 pass on the current router.
- **Why:** A-014 makes `to_ingredients` return ingredients outside the bucket universe (ezetimibe, clavulanate). These tests pin that such names and the label strengths never reach the cloud (I3), and that a flag for another drug never makes the question `known` (I4).
- **Class:** Advances
- **Plan:** advances I3, I4, F4, M5
- **Contract impact:** none
- **Affects:** none. A: nothing to do. When PR #5 merges, the real `to_ingredients` gives the same ingredient sets as the stand-in.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 632 passed, 4 skipped. `check_ownership.py --range origin/main..HEAD` → ownership ok.
- **Inbox:** D 1518 (pack confirmed, gate 20/0/0). Handled, nothing to do. Read A-014, C-021, D-011: no change needed from B.
- **Next:** G2 merge of PR #2. After PR #6 merges, rebase onto v1.3 and confirm test_committed_pack runs, not skips.

### B-029 · 2026-11-08 15:55 · commit `3260352` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** New `tests/B/test_pack_same_for_all.py` (2 tests). A second synthetic patient, "Bea" (warfarin, metformin, amiodarone; VKORC1/CYP2C9; INR, eGFR; sulfa allergy; I1), syncs the pack from a cold device next to Alex. (1) Both send every bucket once, as `cover`, with the same outbound text, the same `bytes_out` and 0 personal fields. Per bucket the traffic is byte-identical, and only the shuffled order differs. (2) None of Bea's rsIDs, phenotypes, conditions, allergy or lab values appear in what is sent, even though some of her meds are in the bucket universe. No router code changed.
- **Why:** The integrator's G4 note to D (20261108-1520) says E1 should show `sync_pack` traffic scoring at chance because it is the same for every user. This test pins that property at the unit level, so a later change that lets the profile shape the sync fails here before the eval runs.
- **Class:** Advances
- **Plan:** advances I5, I3, E1, F8; stretch pack sync
- **Contract impact:** none
- **Affects:** D: E1 can cite this test for "sync traffic is user-independent". A, C, I: none.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 634 passed, 4 skipped. `check_ownership.py --range origin/main..HEAD` → ownership ok.
- **Inbox:** nothing new. Read I's 1520 notes to C and D: they match B's plan (C drops stand-ins for `route`, `feed` and `sync_pack` at G2).
- **Next:** G2 merge of PR #2. After PR #6 merges, rebase onto v1.3 and confirm test_committed_pack runs, not skips.

### B-030 · 2026-11-08 15:28 · commit `28e5edf` · PLAN v1.3

- **Change:** New `tests/B/test_brand_questions.py` (21 tests) runs against A's real `normalize.to_ingredients`, which is now on main. Five brand-name questions are covered: Advil + Plavix, Prilosec + Plavix, Plavix + Protonix, Zestril + Aleve, Bayer low dose + Plavix. For each one: (1) it maps to the exact ingredient key; (2) online, no brand string and no question text leave the device, with 0 personal fields; (3) the named pair leads `Answer.facts` (B-026); (4) asking again is local, 0 B. "Advil with my Plavix" also sends byte-identical traffic to "ibuprofen with my clopidogrel". No router code changed.
- **Why:** D listed brand-name cases as optional red-team work (D 1518). With the real normalizer on main, this can be pinned at the unit level.
- **Class:** Advances
- **Plan:** advances I3, I4, F4, M5
- **Contract impact:** none
- **Affects:** D: the brand-name case is covered in tests/B. E1/E3 can cite it, and nothing is required. A: the test depends on `to_ingredients` brand mapping (Advil, Prilosec, Protonix, Zestril, Aleve, Bayer). FYI only. C, I: none.
- **Demo impact:** none (supports S6 "Plavix with Protonix")
- **Tests:** `make test` exit 0, 658 passed, 1 skipped (the skip waits for A's allergy engine, PR #5). `check_ownership.py --range origin/main..HEAD` → ownership ok.
- **Inbox:** C 1526 (B-025 option done in `/api/ask`). Handled, nothing to do. Read D-030, D-031 (mock CYP2D6 not_assessed): B tests are still green. Read A-015, C-022: no effect on B.
- **Next:** G2 merge of PR #2. After PR #5 merges, rebase and confirm the allergy test in test_g2_real_rules runs.

### B-033 · 2026-11-08 15:36 · commit `71f2d28` · PLAN v1.3

- **Change:** New `tests/B/test_app_path.py` (5 tests). No B code changed. The integrator merged PR #2 (B) and PR #3 (C) at G2. These tests check B's guarantees through C's real `/api/ask` path, not by calling `route()` directly. Cloud is replayed from a temp cache (DEMO=1). (1) Ten questions: C's 4 chips, the discharge-list question, and brand, combination, local-only and allergy questions. Every text that left passes `check_outbound` with the real profile, with no genotype strings. Each send is a whole bucket of 8 distinct topics, `personal_fields_sent` is 0, and the `/api/ledger` totals match. (2) `/api/ledger/{seq}/outbound` returns exactly `ledger.outbound(seq)`. (3) Asking again is a KB hit with 0 new bytes. (4) With `/api/offline` on, no question sends anything. (5) Every app answer passes `wording_problems`.
- **Why:** G2 ("one question end to end"), now with both halves on main. Until now I3 was only pinned at `route()`. This pins it at the app boundary, where C builds the flags.
- **Class:** Advances
- **Plan:** advances G2, I3, I5, I7, I8, F5, F6, F8, S4, S6
- **Refinements:** none
- **Contract impact:** none
- **Affects:** C: no action needed. The test pins `/api/ask`, `/api/ledger/{seq}/outbound` and `/api/offline` against real B code, so a change there that leaks or mis-shows traffic now fails `tests/B` too (message sent). D: E1 can cite it, nothing required. A, I: none.
- **Demo impact:** none (supports S4 ledger view and S6 offline)
- **Tests:** `make test` exit 0: 794 passed, 3 skipped. `check_ownership.py --range origin/main..HEAD`: ownership ok. PR #7 opened.
- **Inbox:** nothing new. Read A-017: nothing for B. PLAN still v1.3, DECISIONS still D-031.
- **Next:** PR #7 review. After PR #5 (A) merges, rebase and confirm the allergy test in test_g2_real_rules runs on main. After PR #4 (D) merges, run eval/queries.json through the app path.

### B-034 · 2026-11-08 15:40 · commit `079b32e` (PR #7) · PLAN v1.3.1

- **Change:** New `tests/B/test_app_pack_path.py` (5 tests). No B code changed. This is G3 prep: the knowledge pack (D-027) checked through C's real `POST/GET /api/sync`, not by calling `sync_pack()` directly. Cloud is replayed from a temp cache (DEMO=1). (1) One sync sends every bucket of the partition exactly once, none blocked, and the app records all of those rows in `_pack_seqs` (I5: same for every user). (2) Every pack row in `/api/ledger` is `kind=cover`, `pack=true`, `personal_fields_sent=0`. Its `/outbound` texts are 8 distinct topics that pass `check_outbound` with the real profile (I3), and `mine` is always empty. (3) After a sync, every partition key is in the KB. With `/api/offline` on, the demo questions all answer with `sent_to_cloud=false` and 0 new bytes (F6, F8, S6). (4) A second sync skips every bucket and sends 0 bytes. (5) `/api/sync` while offline returns 409 and nothing leaves.
- **Why:** The next gate is G3 (17:30, KB + knowledge pack). Until now the pack was only pinned at `sync_pack()`. These tests pin it at the app boundary, where C runs it in a thread and labels the rows.
- **Class:** Advances
- **Plan:** advances G3, F5, F6, F8, S4, S6; I3, I5, I8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** C: no action needed. `tests/B` now also fails if `/api/sync`, the `pack` label or `mine` on pack rows drift (message sent). D: E4c can cite this as the app-level counterpart. A, I: none.
- **Demo impact:** none (supports the S6 "Sync knowledge pack" then Offline beat)
- **Tests:** `make test` exit 0: 799 passed, 3 skipped. `check_ownership.py --range origin/main..HEAD`: ownership ok. PR #7 updated (head 079b32e).
- **Inbox:** integrator 1535 (G2 passed, D-032, PLAN v1.3.1): rebased, re-read PLAN, nothing changes for B. Read A-018 and C-023: nothing for B. C-023's pack and cover rows are grouped in the UI only. The `/api/ledger` entries and `pack` flag that B's tests use are unchanged.
- **Next:** PR #7 review before G3. After PR #5 (A) merges, confirm the allergy test runs. After PR #4 (D) merges, run eval/queries.json through the app path.

### B-035 · 2026-11-08 15:43 · commit `0163ba9` (PR #7, rebased, no new code) · PLAN v1.3.1

- **Change:** No code changed. This was a G4 dry run: D's `eval/` and `docs/` from `origin/agent/D-eval` (PR #4, head 5112526), laid over my branch (main + PR #7) in a scratch worktree, with `make eval` run there. The scratch worktree is deleted, and nothing was committed to D's paths. Results with `DEMO=1`: **G4 gate 20 pass, 0 warn, 0 fail.** Backend `live`, partition `real:data/buckets/v5.json`. E2 live: 11 cloud calls for 20 questions, of which 4 fall in the first five questions and 0 in the last five. Q19 is a KB hit with 0 B sent. E3 live hybrid: 11 calls, 11,111 bytes (about 1,010 B per bucket, against the 1,440 placeholder), 0 personal fields. E4: cold 11/20, warm 18/20, synced pack 18/20, unbacked_known empty, 20/20 cold answers in the expected state. The 2 that stay no_data offline are expected by design: Q03 (`CYP2D6:not_assessed|codeine`) and Q16 (St. John's wort, outside the universe).
- **Finding:** Without `DEMO=1` and without an API key, `cloud.status()` reports offline. The "live" run then sends nothing: E2 shows 0 calls, and E4 shows cold, warm and synced all at 11/20. The gate still passes, but the numbers understate the design. The G4 run must use `DEMO=1 make eval` (or a real key).
- **Why:** This is the BRIEF follow-up: "after PR #4 merges, run eval/queries.json through the app path". It ran early, against the branch, so B-side problems show up before G4 (18:15).
- **Class:** Advances (verification only)
- **Plan:** supports G4, E2, E3, E4; I3, I4, I5, I8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** D: run G4 with `DEMO=1`. You can replace `BYTES_PER_BUCKET=1440` with the measured ~1,010 B, or keep the live ledger number (message sent). I: once PR #4 and PR #7 merge, the gate is expected to pass on main as-is. A, C: none.
- **Demo impact:** none
- **Tests:** `make test` exit 0: 799 passed, 3 skipped. In the scratch worktree, `make eval DEMO=1`: gate 20/0/0.
- **Inbox:** nothing new since B-034. PLAN v1.3.1, DECISIONS D-032, logs A-018, C-023 and D-011 unchanged.
- **Next:** PR #7 review before G3. After PR #5 (A) merges, confirm the allergy test runs. After PR #4 merges, re-run `DEMO=1 make eval` on main.

### B-036 · 2026-11-08 15:55 · commit `f3a4abc` (PR #7) · PLAN v1.3.1

- **Change:** `tests/B/test_app_path.py` and `tests/B/test_app_pack_path.py` no longer skip the whole file when the app falls back to stand-ins. Each now has an explicit test that the app uses the real `router.route`, the real ledger and `sync_pack`, so a regression fails instead of skipping. `LEDGER_IS_MOCK` is read with `getattr(..., False)`, so C can delete the constant.
- **Why:** The real router and ledger have been on main since G2 (D-032), so the skip guards could now only hide a regression. C-024 (PR #8) removed the app's mock fallbacks and kept `LEDGER_IS_MOCK = False` only for B's tests.
- **Class:** Refines (tests in B's own scope)
- **Plan:** supports I3, F5, F8 (app-path coverage)
- **Refinements:** none (test hardening only)
- **Contract impact:** none
- **Affects:** C: you can drop `LEDGER_IS_MOCK` whenever you like (message sent). A, D, I: none.
- **Demo impact:** none
- **Tests:** `make test` exit 0: 801 passed, 3 skipped. In a throwaway merge with `origin/agent/C-app-ui` (PR #8), both files pass: 12 passed. PR #7 updated (head f3a4abc).
- **Inbox:** C 1543 (stand-ins gone, PR #8) handled by this change. D-033 (Gabe is the integrator, backup Dhiaa): noted. Read A-019 and C-024: nothing else for B.
- **Next:** PR #7 review before G3 (17:30). After PR #5 merges, confirm the allergy test runs. After PR #4 merges, re-run `DEMO=1 make eval` on main.

### B-037 · 2026-11-08 15:50 · commit `5db1721` (PR #7, rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #7 onto main (`aa30bbf`, D-034) and force-pushed it (new head `5db1721`). Then I checked early that B's allergy test runs against A's allergy engine. In a throwaway worktree I merged PR #7 with `origin/agent/A-data-rules` (PR #5, `d81a2b0`). There were no conflicts, and `make test` exited 0 with 1090 passed and 2 skipped. On PR #7 alone it is 801 passed and 3 skipped. Skip reasons cannot be printed in this sandbox, so this is by elimination. Merging #5 removes exactly one skip, and the only B skip that waits on #5 is `test_g2_real_rules.py`'s allergy test. So that test now runs and passes: amoxicillin stays local_only, 0 bytes, 0 personal fields (I3). I removed the worktree and pushed nothing from it.
- **Why:** The BRIEF queue is done and PR #7 is waiting for review. This settles one of my post-merge checks before G3 (17:30), not after it.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I3
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #7 head is now `5db1721`, and #7 + #5 merge cleanly and stay green. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped. On PR #7 + PR #5: exit 0, 1090 passed, 2 skipped.
- **Inbox:** nothing new for B. D-034 (submission draft, personalization described as rule-based): noted, B's claims (I3, ledger bytes, offline) are unaffected. A-020 (G3 rehearsal on four PR heads, 1154 green): matches this check.
- **Next:** PR #7 review and merge at G3. After PR #4 (D) merges, re-run `DEMO=1 make eval` on main.

### B-038 · 2026-11-08 16:00 · commit `4101ae2` (PR #7, rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #7 onto main `6c35c51` (A-021, D-012) and force-pushed it (new head `4101ae2`). Then I answered D's open question from D-012 (A-016) with what B's router actually does. Offline, a question that a local flag covers but whose cloud key is not in the KB yet returns `state="no_data"` with `OFFLINE_TEXT`, sends 0 bytes and writes no ledger entry. This is deliberate under I4: an open cloud key is never shown as "checked". `tests/B/test_offline.py::test_offline_cold_kb_is_no_data_zero_bytes_no_ledger` pins it. The flag itself still comes from `rules.check_all`, and C's UI shows it either way. So D's plan to report both readings (what the user sees, and the router state) matches the code. B will not change this without a proposal.
- **Why:** D-012 left the A-016 question open and waiting for D's human owner. The facts on B's side help that decision. The BRIEF queue (stretch included) is done.
- **Class:** Advances
- **Plan:** supports F8, I4, P7 E4 reporting; G3 (P9) prep
- **Refinements:** none
- **Contract impact:** none
- **Affects:** D: the router-state reading of E4 is pinned by a B test you can cite (message sent). I: PR #7 head is now `4101ae2`. A, C: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped.
- **Inbox:** D 1551 (P3 added; D cites B's brand and sync tests and uses about 1,010 B per group from the live ledger) handled, no action for B. Read A-021: G3 sequence green on the integrated heads (#4, #5, #7, #8), nothing for B. D-012: see above.
- **Next:** PR #7 review and merge at G3 (17:30). After PR #4 merges, re-run `DEMO=1 make eval` on main.

### B-039 · 2026-11-08 16:10 · commit `079fe75` (PR #7, rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #7 onto main `dba1848` and force-pushed it (new head `079fe75`). Then I ran a G3 merge rehearsal on the newest heads of all four open PRs. C's PR #8 changed after my app-path tests (B-033, B-034, B-036) were written, so I wanted to check them against it. In a throwaway worktree at main `dba1848` I merged PR #7 (`4101ae2`, same code as `079fe75`), PR #8 (`ff5a93c`), PR #5 (`1349212`) and PR #4 (`0598ceb`) in one octopus merge. Git hit no conflicts. `make test` exited 0 with 1157 passed and 0 skipped, so every B app-path test, the allergy test included, runs and passes on the merged tree. I removed the worktree and pushed nothing from it.
- **Why:** The BRIEF queue is done and PR #7 is waiting for review. This lets the integrator merge for G3 (17:30) in any order without a surprise from B's side.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I3, I4, F8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #7 head is now `079fe75`. #4 + #5 + #7 + #8 merge cleanly on main and stay green (message sent). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped. On main + #7 + #8 + #5 + #4: exit 0, 1157 passed, 0 skipped.
- **Inbox:** nothing new for B. No new DECISIONS (still D-034), PLAN still v1.3.1, and no new A, C or D LOG entries since B-038.
- **Next:** PR #7 review and merge at G3 (17:30). After PR #4 merges, re-run `DEMO=1 make eval` on main.

### B-040 · 2026-11-08 16:20 · commit `1e265c1` (PR #7, rebase only, no new code) · PLAN v1.3.2

- **Change:** No code changed. I rebased PR #7 onto main `c2518bc` (D-035, PLAN v1.3.2) and force-pushed it (new head `1e265c1`). I re-ran the G3 merge rehearsal because PR #5 (A) and PR #4 (D) heads moved. In a throwaway worktree at main `c2518bc` I octopus-merged PR #7 `1e265c1`, PR #5 `f483847`, PR #8 `ff5a93c` and PR #4 `4bd66e2`. Git hit no conflicts. `make test` exited 0 with 1158 passed and 0 skipped. A force-pushed #5 while I was running, so I first ran the merge with `1349212` (1158 passed, 0 skipped), then ran it again with `f483847`. I removed the worktree and pushed nothing from it.
- **Not run:** the D-035 G4 command (`DEMO=1 make eval && python -m eval.gate`). The sandbox refused `make eval` in the throwaway tree. D-013 reports 22/0/0 on D's tree. The integrator should run it on main after G3.
- **Why:** G3 is at 17:30 and two heads moved after B-039. The integrator should merge a set of heads that has been tested together.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I3, I4, I7, F8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #7 head is now `1e265c1`. The current heads #4 `4bd66e2`, #5 `f483847`, #7 `1e265c1` and #8 `ff5a93c` merge cleanly on main and stay green (message sent). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped. Integrated: exit 0, 1158 passed, 0 skipped. `python -m core.cloud check`: 136/136 keys usable, 0 missing, 0 rejected (I7), 0 outside the partition.
- **Inbox:** D 1600 (E4 strict reading equals `route()` state, cold 4/20, synced 18/20): handled, nothing for B. D-035 (G4 command) and PLAN v1.3.2: read, no change to B's code. Read D-013 and A-022: nothing for B.
- **Next:** PR #7 review and merge at G3 (17:30). After G3, rebase onto main and run B's suite against the merged code. Run the D-035 G4 command on main if the sandbox allows it.

### B-041 · 2026-11-08 16:35 · commit `91a39b7` (PR #7, rebase only, no new code) · PLAN v1.3.2

- **Change:** No code changed. I rebased PR #7 onto main `f51ae85` and force-pushed it (new head `91a39b7`, same code as `1e265c1`). Main only gained coordination commits since B-040, so the G3 rehearsal from B-040 and A-023 still holds for this code.
- **Why:** keep PR #7 current on main before the G3 merge (17:30). Every BRIEF queue item and the stretch item are done, so nothing else is unblocked for B before G3.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I3, I4, F8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #7 head is now `91a39b7` (code identical to `1e265c1`, which A-023 and B-040 tested together with #4, #5 and #8). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped. CI checks on the PR: green.
- **Inbox:** nothing new for B. No new DECISIONS (still D-035), PLAN still v1.3.2. Read A-023 (G3 rehearsal 1158 passed, gate 22/0/0) and D's STATUS update: nothing for B.
- **Next:** PR #7 review and merge at G3. After G3, rebase onto main, run B's suite against the merged code, and run the D-035 G4 command on main if the sandbox allows it.

### B-042 · 2026-11-08 16:45 · commit `e269240` (PR #7, rebase only, no new code) · PLAN v1.3.2

- **Change:** No code changed. I rebased PR #7 onto main `0ed2e0c` and force-pushed it (new head `e269240`, same code as `1e265c1` and `91a39b7`). Main only gained one coordination commit (integrator inbox to A, C, D on vision-model labels), so the B-040 and A-023 G3 rehearsal still holds for this code.
- **Why:** keep PR #7 current on main before the G3 merge (17:30). Every BRIEF queue item and the stretch item are done.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I3, I4, F8
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #7 head is now `e269240` (code identical to the tested `1e265c1`). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on PR #7: exit 0, 801 passed, 3 skipped.
- **Inbox:** nothing new for B. No new DECISIONS (still D-035), PLAN still v1.3.2. Read `0ed2e0c` (vision-model label results to A, C, D): label capture is outside B's paths, nothing for B.
- **Next:** PR #7 review and merge at G3. After G3, rebase onto main, run B's suite against the merged code, and run the D-035 G4 command on main if the sandbox allows it.

### B-043 · 2026-11-08 16:55 · commit `87d6e0a` (main after PR #4, #5, #7, #8 merged; no new B code) · PLAN v1.3.2

- **Change:** No code changed. PR #7 is merged (`1ceb00a`), and so are #5, #8 and #4 (main `87d6e0a`). I rebased `agent/B-privacy-router` onto main (it now equals main) and force-pushed it. I then ran B's suite and the D-035 G4 command on the integrated main.
- **Why:** this is the post-merge check from B-042's "Next" line (AGENTS.md §11: after merges, switch from mocks to real code and re-test).
- **Class:** Advances
- **Plan:** advances G3/G4 (P9); I3, I4, F8 checked on the integrated build
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: main `87d6e0a` is green for B, and the G4 gate passes on it (numbers below). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on main `87d6e0a`: exit 0, 1158 passed, 0 skipped. `make eval DEMO=1` then `python -m eval.gate`: **G4 gate 22 pass, 0 warn, 0 fail** (P1 real v5 partition, P3 demo replay, E2a 11 calls / 20 questions, E3c 0 personal fields, E4a cold 11/20 warm 18/20, E4c synced 18/20, I4 none, I7b 25/25). The eval rewrote `docs/results.md` and `eval/results/latency_cost.json` in my worktree; I reverted both (D owns them) and committed nothing.
- **Inbox:** nothing new for B. No new DECISIONS (still D-035), PLAN still v1.3.2. Read A-024 (standalone gate 22/0/0): matches this run.
- **Next:** B's queue and the stretch item are done and on main. Wait for the G3 ruling and the next PLAN version, and answer any inbox requests. The local Finder copies (`core/cloud 2.py` etc.) are untracked; a human can delete them.

### B-044 · 2026-11-08 17:05 · commit `d74c0b5` (PR #10, tests only) · PLAN v1.3.3

- **Change:** two new tests in `tests/B/test_pack_sync.py` for C-025's "Not done" item: one stage-delay Sync stopped after 1 group with `offline: true`, and it didn't happen again. (1) With `DEMO=1` and `GV_DELAY_S=0.3,2.0`, a sync sends every group: 8 pauses per group, each between 0.3 and 2.0 s. (2) Wi-Fi switched off halfway through the first group: that group finishes and its answers are kept in the KB, the rest are not tried, and the result is `sent=1, offline=true`. After Wi-Fi comes back, the next sync skips the stored group and sends the rest, so each group is sent once overall.
- **Why:** with demo mode on, `cloud._answers` raises `CloudUnavailable` only when `offline()` is forced, so a demo-mode `offline: true` always means `GV_OFFLINE` or `/api/offline` (the S6 toggle) was on while the sync was still running. A Sync with stage delays takes about 2 min, so pressing S6 Wi-Fi off before it finishes gives exactly C's result. That is correct behaviour (F8), not a bug.
- **Class:** Advances
- **Plan:** advances F6, F8, P6.6, S6; I5 (whole buckets, each once)
- **Refinements:** none
- **Contract impact:** none
- **Affects:** C: explains C-025's one-group Sync, nothing to change (the "Went offline; what arrived is kept" UI is right). D: rehearsal note: with stage delays, wait for Sync to finish before S6 Wi-Fi off.
- **Demo impact:** S6 timing note only (no click changes)
- **Tests:** `make test` on main `b1ca51c` + this commit: exit 0, 1160 passed.
- **Inbox:** to-B/20261108-1605-from-integrator-g3-passed.md (G3, PLAN v1.3.3, D-036): nothing changes for B. Read C-025, D-014.
- **Next:** PR #10 for the integrator before G4 (18:15). Then answer inbox requests until G5 freeze.

### B-045 · 2026-11-08 16:10 · commit `82032ff` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (the B-044 tests) was rebased onto main `c673542` and pushed as `82032ff`. Before that I checked it together with A's PR #9: merging main + #9 + #10 in a throwaway worktree gave no conflicts.
- **Why:** to keep PR #10 ready to merge before G4, and to show that the two open non-draft PRs (#9 and #10) can merge in either order.
- **Class:** Advances
- **Plan:** advances F8, S6 (same as B-044); no change to any invariant
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 (CI green) and PR #9 can merge together, so both can go in at G4. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch (main `c673542` + `82032ff`): exit 0, 1160 passed. On the throwaway merge of main + PR #9 + PR #10: exit 0, 1166 passed. The throwaway worktree was removed afterwards.
- **Inbox:** nothing new for B. Read A-025 (capture vision-model hint, PR #9): it touches only `core/capture.py` and does not change any input to the router. No new DECISIONS (D-036), PLAN still v1.3.3.
- **Next:** PR #10 merge at G4. Then answer inbox requests until G5 freeze.

### B-046 · 2026-11-08 16:20 · commit `f8c7fe1` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (B-044 tests) was rebased onto main `8946465` and pushed as `f8c7fe1`. Main moved only in `coord/` since `c673542`. I then merged main with all four open PRs in a throwaway worktree: #9 A `cf3df82`, #10 B `f8c7fe1`, #11 C `ad4300f`, #12 D `3fcab5a` (draft). There were no conflicts.
- **Why:** G4 is at 18:15 and freeze is at 18:30. The integrator can merge #9 to #12 in any order without a surprise.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); F8, S6 unchanged; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: #9, #10, #11 and #12 merge together cleanly and the suite is green. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch: exit 0, 1160 passed. On the throwaway merge of main + #9 + #10 + #11 + #12: exit 0, **1171 passed**. The throwaway worktree was removed. Not run: the D-035 G4 eval command on the combined build. The integrator should run it at G4.
- **Inbox:** nothing new for B. Read D-037 (D's offline two-reading line accepted; it matches B-038/B-043 numbers, nothing for B), A-026 (PR #9 rebase only) and C-026 (`/api/status.vision.configured`, does not touch the router).
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

### B-047 · 2026-11-08 16:35 · commit `b1a94ad` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (B-044 tests) was rebased onto main `565cbcb` and pushed as `b1a94ad`. Main moved only in `coord/` since `8946465` (A-027, B-046, C-026 reports and C's PR #11 ready note). Heads of #9 (`cf3df82`), #11 (`ad4300f`) and #12 (`3fcab5a`) are unchanged since B-046, so the B-046 merge-clean result still holds. I did not repeat the throwaway merge.
- **Why:** keep PR #10 current for G4 (18:15).
- **Class:** Advances
- **Plan:** advances G4 prep (P9); F8, S6 unchanged; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head is now `b1a94ad`. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch: exit 0, 1160 passed. PR #10 CI re-runs on the new head.
- **Inbox:** nothing new for B. Read A-027 (PR #9 re-check, no re-push) and C-026 (PR #11 ready). Neither touches the router.
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

## B-048 PR #10 rebased onto 16dbc59, 1160 green

- **What changed:** PR #10 (tests only) rebased onto main `16dbc59`. Main moved by coord-only commits (A-028, D-015, B-047), so no code under core/, tests/, data/ or app.py changed. New head `6dc7f25`.
- **Class:** Advances (rebase only). **Plan:** keeps S6 / P6 offline pins (B-044) current for G4. **Contract:** none.
- **Affects:** I: PR #10 head is now `6dc7f25`. A, C, D: nothing to do.
- **Demo impact:** none. D-015 (D's reply to-B/20261108-1617) moved the S6 "let Sync finish before Wi-Fi off" step into the script. That matches B-044. Nothing for B to change.
- **Tests:** `make test` on the branch: exit 0, 1160 passed.
- **Inbox:** handled 20261108-1617-from-D-sync-line.md. Read A-028 (PR #9 re-check) and D-015. Neither touches B's code.
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

### B-049 · 2026-11-08 16:45 · commit `abc231a` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (B-044 tests) rebased onto main `42a520b` and pushed as `abc231a`. Main moved only in `coord/` since `16dbc59` (A-029, A-030, B-048, C-027). `git diff` from the old head to the new one, outside `coord/`, is empty.
- **Why:** keep PR #10 current for G4 (18:15).
- **Class:** Advances
- **Plan:** advances G4 prep (P9); F8, S6 unchanged; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head is now `abc231a`. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037. Read C-027 (hero title on scroll, PR #11, UI only) and A-029/A-030 (PR #9 re-checks). None touch the router.
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

### B-050 · 2026-11-08 16:55 · commit `86cb882` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (B-044 tests) rebased onto main `7d8e02a` and pushed as `86cb882`. Main moved only in `coord/` since `42a520b` (B-049, integrator pass `3973735`, A-030 status).
- **Why:** keep PR #10 current for G4 (18:15).
- **Class:** Advances
- **Plan:** advances G4 prep (P9); F8, S6 unchanged; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head is now `86cb882` (the 16:22 to-human note lists `6dc7f25`; content is the same, tests only). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037. Read integrator pass `3973735` (G4 merges escalated to Gabe). Nothing for B to do.
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

### B-051 · 2026-11-08 16:26 (system clock; B-050's 16:55 stamp was wrong) · commit `a68211a` (PR #10, rebase only) · PLAN v1.3.3

- **Change:** no code change. PR #10 (B-044 tests) rebased onto main `4960c3b` and pushed as `a68211a`. Main moved only in `coord/` since `7d8e02a` (B-050 report, A-030 status).
- **Why:** keep PR #10 current for G4 (18:15).
- **Class:** Advances
- **Plan:** advances G4 prep (P9); F8, S6 unchanged; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head is now `a68211a` (same content, tests only). A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on the branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4. Then hold for freeze and answer inbox requests.

### B-052 · 2026-11-08 16:28 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by B's own B-051 report (`3a59953`, coord-only). Branch rebased locally (`b4709df`) and re-tested; PR #10 not re-pushed because its head `a68211a` is green (2/2 checks) and mergeable, and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-053 · 2026-11-08 16:40 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by coord-only reports (`ba0b144` C STATUS, `20606ab` B-052, `8d3c339` A STATUS). Branch rebased locally (`447b972`) and re-tested; PR #10 not re-pushed because its head `a68211a` is green (2/2 checks) and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-054 · 2026-11-08 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by coord-only reports (`ae8b2fd` B-053, `7766f85` A STATUS). Branch rebased locally (`3d79e02`) and re-tested; PR #10 not re-pushed because its head `a68211a` is green (2/2 checks) and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-055 · 2026-11-08 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by coord-only reports (`61e7c0a` B-054, `f18a179` A STATUS). Branch rebased locally (`ab6ebae`) and re-tested; PR #10 not re-pushed because its head `a68211a` is green (2/2 checks) and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-056 · 2026-11-08 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by coord-only reports (`c095b5a` B-055, `a1e2851` A STATUS). Branch rebased locally (`8f5d5e5`) and re-tested; PR #10 not re-pushed because its head `a68211a` is green (2/2 checks) and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-057 · 2026-11-08 · no push (PR #10 stays at `a68211a`) · PLAN v1.3.3

- **Change:** none. Main moved only by coord-only reports (`eca9e08` B-056, `d88ebdc` A STATUS). Branch rebased locally (`c44ef6b`) and re-tested. PR #10 not re-pushed: its head `a68211a` is green (2/2 checks), and a re-push would only restart CI.
- **Why:** keep PR #10 verified for G4 (18:15) without churn.
- **Class:** Advances
- **Plan:** advances G4 prep (P9); no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #10 head still `a68211a`, ready to merge. A, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on rebased branch: exit 0, 1160 passed.
- **Inbox:** nothing new for B. PLAN still v1.3.3, last decision still D-037, no new proposals. No FREEZE, no STOP.
- **Next:** PR #10 merge at G4; re-push only if main changes code. Then hold for freeze and answer inbox requests.

### B-058 · 2026-11-08 · commit `ccf2c4f` (PR #10) · PLAN v1.3.4

- **Change:** `core/router.py` `route()`: when the question names drug pairs and none of them has a fact or a flag on that exact pair, the answer is `no_data` (NO_DATA_TEXT, or OFFLINE_TEXT when offline), with no facts. Before, a flag sharing one drug made "Is pantoprazole okay with my lisinopril?" answer `known` with LOCAL_TEXT ("checked on your device"). Substitution questions ("naproxen instead of ibuprofen", "rather than", "switch") keep the old rule, as pinned by `test_covering_class_rule_flag_is_known_even_with_out_of_partition_pair`. 3 new tests in `tests/B/test_app_path.py` (uncovered pair online, offline, and `clopidogrel|pantoprazole` still `known`).
- **Why:** owner report `20261108-1645-from-human-uncovered-pair-reads-checked.md`: "checked" reads as "nothing found", the reassurance I4/I7 forbid. A judge can type exactly this kind of pair.
- **Class:** Advances (bug fix, allowed under G5 rules)
- **Plan:** advances I4, I7, P6.1; no invariant weakened (one is tightened)
- **Refinements:** a named pair is "taken together" unless the question uses substitution wording (instead of / rather than / in place of / replace / switch).
- **Contract impact:** none (same Answer fields and states)
- **Affects:** C: nothing to change. merge already shows the no_data lead and still lists high flags ("Separately, your flagged items X1 and X2 ..."). D: I4 eval unchanged; gate re-run green. I: PR #10 now carries this fix (head `ccf2c4f`), please merge before freeze.
- **Demo impact:** an off-list pair typed live now reads "no data" instead of "checked". No S-beat script changes.
- **Tests:** `make test` exit 0, 1163 passed. `make eval DEMO=1 && python -m eval.gate`: 22 pass, 0 warn, 0 fail (generated docs/eval files reverted, not committed).
- **Next:** hold PR #10 for merge; answer inbox until G5 freeze (18:30).

### B-059 · 2026-11-08 16:47 · commit `41f5912` (branch = main, no new code) · PLAN v1.3.4

- **Change:** No code changed. PR #10 (including the B-058 I4 fix `ccf2c4f`) was merged into main as `c59a2c5`, together with #9, #11 and #12. I rebased onto main `41f5912`. My branch now equals main, and `origin/agent/B-privacy-router` was fast-forwarded to it.
- **Why:** sync after the G4 merges (cycle step 1). My BRIEF queue is done, and I am adding no code on the demo path before the G5 freeze (18:30).
- **Class:** Advances
- **Plan:** advances G4/G5 prep (P9); I4, I7, P6.1, P6.6 unchanged
- **Refinements:** none new. The B-058 line (a named pair is "taken together" unless the question uses substitution wording) is still waiting to be folded into PLAN.
- **Contract impact:** none
- **Affects:** I: B has no open PR. Nobody else needs to act.
- **Demo impact:** none. D-039 (Codespaces) uses B's existing `GV_COVER_INTERVAL_S` setting (`core/router.py`) set to 20. Any value above 0 is accepted. Cover traffic stays on (P6.6).
- **Tests:** `make test` on main `41f5912`: exit 0, 1177 passed.
- **Inbox:** no new messages for B. Read D-039, A-030, C-028 and D-016. None of them needs anything from B.
- **Next:** hold for freeze and answer inbox requests.

### B-060 · 2026-11-08 · commit `c4c4998` (PR #15, tests only) · PLAN v1.3.4

- **Change:** I added one test, `test_codespaces_interval_20s` in `tests/B/test_cover_delays.py`. With `GV_COVER_INTERVAL_S=20` (the D-039 Codespaces value), `router.cover_interval()` returns 20. Over 200 ticks, the cover loop waited between 10 and 30 s each time (20 × uniform(0.5, 1.5)), the waits were jittered rather than fixed, and each tick sent exactly one whole bucket. No code in `core/` changed.
- **Why:** this answers the integrator's message `20261108-1644-from-integrator-codespaces-cover-interval.md` with a test, not just a statement. 20 s breaks no assumption in the router: rate, jitter and the uniform draw over the fixed partition (I5, E1) do not depend on the interval.
- **Class:** Advances
- **Plan:** advances P6.6, D-039; no invariant touched
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PR #15 is tests only and safe to merge before G5. Nobody else needs to act.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1178 passed.
- **Inbox:** no new messages. Nothing new in PLAN, DECISIONS or the other agents' LOGs since B-059.
- **Next:** hold for the G5 freeze (18:30) and answer inbox requests.

### B-061 · 2026-11-08 · commit `c4c4998` (PR #15, unchanged) · PLAN v1.3.4

- **Change:** No code changed. Main moved only by coord reports (`b05ad09` D, `6895a77` B-060, `c7f159f` A) since B-060. I rebased locally (exit 0) and re-tested. PR #15 stays at `c4c4998` (2/2 checks green), no re-push.
- **Why:** cycle sync (step 1). BRIEF queue is done; no new demo-path code before the G5 freeze (18:30).
- **Class:** Advances
- **Plan:** advances G5 prep (P9); no invariant touched
- **Refinements:** none new (B-058 line still waiting to be folded into PLAN)
- **Contract impact:** none
- **Affects:** I: PR #15 (tests only) still ready to merge. Nobody else needs to act.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1178 passed.
- **Inbox:** no new messages. No new PLAN version, DECISIONS (last D-039) or LOG entries (A-030, C-028, D-016).
- **Next:** hold for the G5 freeze and answer inbox requests.

### B-062 · 2026-11-08 16:55 · commit `c4c4998` (PR #15, unchanged) · PLAN v1.3.4

- **Change:** No code changed. Main moved only by coord commits (`2854856` B-061, `95a71d1` A, `4603f3e` proposal) since B-061. Rebased locally (exit 0) and re-tested. PR #15 stays at `c4c4998` (2/2 checks green), no re-push.
- **Why:** cycle sync (step 1). New proposal `20261108-1655-human-adaptive-questions.md` (touches I4, I5) has no integrator ruling yet, so per AGENTS.md §5 B keeps coding against PLAN v1.3.4 and starts nothing from it.
- **Class:** Advances
- **Plan:** advances G5 prep (P9); no invariant touched
- **Refinements:** none new (B-058 line still waiting to be folded into PLAN)
- **Contract impact:** none
- **Affects:** I: PR #15 (tests only) still ready to merge; B is ready to build proposal parts 2 (GV_TAIL) and 3 (GV_DEMO_LIVE_FALLBACK) behind flags, default OFF, once ruled (message sent). Nobody else needs to act.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1178 passed.
- **Inbox:** no new messages. No new PLAN version, DECISIONS (last D-039) or LOG entries (A-030, C-028, D-016).
- **Next:** if the proposal is accepted, build part 3 first (smallest, flag OFF by default), then part 2; otherwise hold for the G5 freeze.

### B-063 · 2026-11-08 17:05 · commit `c4c4998` (PR #15, unchanged) · PLAN v1.3.4

- **Change:** No code changed. Main moved only by coord commits (`87d3ba8` B-062, `31ab9e3` A status) since B-062. Rebased locally (exit 0) and re-tested. PR #15 stays at `c4c4998` (OPEN, MERGEABLE), no re-push.
- **Why:** cycle sync (step 1). Proposal `20261108-1655-human-adaptive-questions.md` (I4, I5) still has no integrator ruling, so B keeps coding against PLAN v1.3.4 (AGENTS.md §5).
- **Class:** Advances
- **Plan:** advances G5 prep (P9); no invariant touched
- **Refinements:** none new (B-058 line still waiting to be folded into PLAN)
- **Contract impact:** none
- **Affects:** I: PR #15 (tests only) still ready to merge. Nobody else needs to act.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1178 passed.
- **Inbox:** no new messages. No new PLAN version, DECISIONS (last D-039) or LOG entries (A-030, C-028, D-016).
- **Next:** if the proposal is accepted, build part 3 (GV_DEMO_LIVE_FALLBACK) then part 2 (GV_TAIL), flags default OFF; otherwise hold for the G5 freeze (18:30).

### B-064 · 2026-11-08 17:15 · commit `0705cbe` (PR #15) · PLAN v1.3.5

- **Change:** D-040 part 3, `GV_DEMO_LIVE_FALLBACK` (default off) in `core/cloud.py`. With `DEMO=1` and the flag set, a bucket with any key missing from the replay cache is asked live when `ANTHROPIC_API_KEY` is set. The whole bucket is sent, never only the missing key (I5), with the live delays (P6.4, default 0.3-2.0 s). Cached (reviewed pack) answers are kept; live answers fill the rest with source `cloud:<model>`. A live failure is logged and degrades to replay only, so misses stay `no_data` (I4). Forced offline still wins. Flag off: demo mode never touches the network (I8). New helper `cloud.demo_live_fallback()`; `pause()` / `delay_range()` take an optional `live` argument (old calls unchanged). 8 new tests in `tests/B/test_demo_live_fallback.py`.
- **Why:** D-040 accepted the adaptive-questions proposal; to-B 20261108-1702 routes parts 2 and 3 to B. Part 3 first (smallest).
- **Class:** Advances
- **Plan:** advances D-040 part 3, P6, F8; I4, I5, I7, I8 kept (flag off = unchanged)
- **Refinements:** live fallback sends every topic of the bucket and keeps cached answers over live ones; a failed live fallback returns replay only.
- **Contract impact:** none (additive env flag and helper)
- **Affects:** C: nothing required; with the flag on, demo facts for keys outside the pack carry source `cloud:<model>` instead of `cloud-cache:<v>`, and `status()` is unchanged. D: eval unaffected with the flag off; partition v5 and the pack are unchanged, so with the flag on and the pack complete no live call happens. I: PR #15 now carries this commit plus the D-039 test pin.
- **Demo impact:** none with the flag off. Flag on only matters once part 2 (GV_TAIL) adds keys outside the pack.
- **Tests:** `make test` exit 0, 1186 passed.
- **Inbox:** handled 20261108-1658 (hold, superseded by D-040) and 20261108-1702 (parts 2-3). No new LOG entries from A, C, D.
- **Next:** part 2, `GV_TAIL`: `data/buckets/tail-v1.json` generator + router tail path + consented single send, flag off unless green by 18:00.

### B-065 · 2026-11-08 17:08 · commit `3403f65` (PR #15) · PLAN v1.3.5

- **Change:** D-040 part 2, `GV_TAIL` (default off). New fixed partition `data/buckets/tail-v1.json`: 1047 buckets of 8 (8376 keys), built once by `data/buckets/build_tail_v1.py` (seed 20261108; generator committed, a test checks the file rebuilds the same). It holds every drug-drug pair over A's ingredient vocabulary (`data/rules/drug_names.json` + core drugs) and one drug-lab key per ingredient and lab (9 labs, one fixed band each), minus every v5 member and alias. Router with the flag on: core first, KB, then the key's tail bucket through every P6 step (generalize, delays, leakage check, ledger `bucket` with bucket_id `tail-NNNN`, all 8 answers stored). A drug-lab key with another band maps to the one tail key of that drug + lab and shares its answer (same topic text, so the band never picks the bucket, I3). Cover ticks pick core or tail by a fair coin, then a uniform bucket (I5). New `router.single_candidates(question, flags)` and `router.send_single(key)` (C's shapes, accepted as written): one generalized topic, leakage check (blocked = 0 bytes), I7 wording check, ledger `bucket` entry with bucket_id `single`; refused (ValueError) for any key either partition holds; flag off or offline = `no_data`, no ledger entry. New `cloud.ask_single(topic)`. 14 new tests in `tests/B/test_tail.py`.
- **Why:** D-040, to-B 20261108-1702 (parts 2-3 for B). The uncovered-pair "checked" fix asked in the same message already shipped in B-058.
- **Class:** Advances
- **Plan:** advances D-040 part 2, P6, I5; I3, I4, I7 kept; flag off = unchanged behaviour
- **Refinements:** tail bands are one fixed band per lab (egfr<60, potassium>5.0, sodium<135, magnesium<1.8, glucose>180, tsh>4.5, alt>120, ck>1000, inr>3.0); other bands alias onto it. No priors exist for tail keys, so no frequency tier: seeded shuffle per family. Ingredient tokens with `_` or spaces (st_johns_wort, penicillin_v, penicillin_g, potassium chloride) are left out of the tail because `topic_for_key` cannot phrase them. Leftover keys share one mixed bucket padded with `drug|ldl>190`. Cover with GV_TAIL: fair coin core/tail.
- **Contract impact:** none (new router/cloud functions; `Answer`, `LedgerEntry`, `Bucket` unchanged; single send uses kind `bucket`, bucket_id `single`)
- **Affects:** C: `single_candidates` / `send_single` exist with your names; ledger prefixes `tail-` (bucket_id and version `tail-v1`) and `single` as you proposed. `single_candidates` is usually `[]`: with the flag on every pair of known ingredients is in the tail, so the consent dialog shows only for a generalizable key outside both partitions. D: tail E1 should load `load_buckets("tail-v1")`; with `GV_TAIL=1` questions naming two non-core ingredients now send a tail bucket (in DEMO=1 they read `no_data` unless the cache has them or `GV_DEMO_LIVE_FALLBACK=1` + key). I: PR #15 now has 3 commits (D-039 pin, part 3, part 2).
- **Demo impact:** none with the flag off. With `GV_TAIL=1` + `GV_DEMO_LIVE_FALLBACK=1` + key, judges' off-script pairs get a live, bucket-hidden answer.
- **Tests:** `make test` exit 0, 1200 passed. Not run: the full suite with `GV_TAIL=1` exported (the sandbox refused env-prefixed pytest); flag-on behaviour is covered by `tests/B/test_tail.py` only.
- **Inbox:** handled 20261108-1702-from-C-single-and-tail-shape (shapes confirmed). New LOG: C-029 (input click fix), nothing for B.
- **Next:** full-suite + eval run with GV_TAIL=1 on main after merge; decide flag ON/OFF by 18:00 with the integrator.

### B-066 · 2026-11-08 17:12 · commit `97f83f3` (PR #15) · PLAN v1.3.5

- **Change:** Ran the full suite with `GV_TAIL=1 GV_DEMO_LIVE_FALLBACK=1 GV_FUZZY=1` (flags set from inside Python) on a throwaway merge of main + PR #15 + #16 (C-030) + #17 (A-032). 10 B tests failed. 3 were real router bugs: with the tail on, a covering local flag no longer settled the question. Tail drug-lab keys and tail-only pairs were sent on top of it, and a cache miss turned the local `known` answer into `no_data`. Cases: allergy flag + "amox-clav"; X3/X4 + "simvastatin dose and my potassium"; class-rule flag + "naproxen instead of ibuprofen"; X1 + "eGFR 48" sent an extra tail bucket. Fix in `core/router.py`: (1) the ingredients of one combination product named in the question ("amox-clav", "ezetimibe-simvastatin") are never a pair; (2) tail drug-lab keys are asked only when no flag covers the question; (3) a substitution question asks no tail-only pair. Named tail pairs are still asked, even beside an unrelated covering flag (the D-040 goal). The other 7 failures were tests that assume the core partition (cover draws, core vocabulary); they now pin `GV_TAIL` off, and 7 flag-on tests were added to `tests/B/test_tail.py`.
- **Why:** B-065 next step (flag-on full suite before the 18:00 ON/OFF call). A wrong `no_data` on an allergy question would be an S-beat regression with the flag on.
- **Class:** Refines
- **Plan:** refines D-040 part 2 (when tail keys are asked); I4, I5, P6.1 kept; flag off = unchanged
- **Refinements:** with GV_TAIL, tail drug-lab keys only when no flag covers the question; same-product ingredient pairs never asked; substitution questions ask no tail-only pair.
- **Contract impact:** none
- **Affects:** C: confirmed `single_candidates(question, flags) -> list[str]`, `send_single(key) -> Answer` (records its own ledger `bucket` entry, bucket_id `single`; blocked = `blocked` entry), tail bucket_id `tail-NNNN`, exactly as C-030 reads them. Nothing to change. D: with GV_TAIL, fewer spurious tail sends; E1 on named tail pairs unchanged.
- **Demo impact:** none with flags off. With them on, local answers (allergy, X3/X4, class rule) stay local in S4/S6.
- **Tests:** `make test` exit 0, 1207 passed (B branch). Throwaway merge main + #15 + #16 + #17: flags off exit 0, 1263 passed; all three flags on exit 0, 1263 passed.
- **Inbox:** handled 20261108-1708-from-C-d040-ui-ready (shapes confirmed). New LOG: A-031/A-032 (`suggest`, PR #17), C-030 (PR #16): no B change needed.
- **Next:** eval with the flags on after merge; recommend flag ON/OFF to the integrator by 18:00.

### B-067 · 2026-11-08 17:24 · commit `414aa1c` (PR #15) · PLAN v1.3.6

- **Change:** New `tests/B/test_d041_contract.py` (tests only): the real `router.single_candidates` / `router.send_single` have the same parameters and type hints as the D-041 stubs in `core/interfaces.py`, and with `GV_TAIL` off they return exactly what the stubs return (`[]`; `no_data`, `sent_to_cloud=False`, no facts) and write no ledger row. PR #15 rebased onto main 8171eb1.
- **Why:** D-041 put both functions in CONTRACTS and asked B to keep the signatures fixed until freeze. This test fails if they drift.
- **Class:** Advances
- **Plan:** advances D-040 part 2, D-041; I3, I5 unchanged
- **Contract impact:** none
- **Affects:** none. I: ON/OFF recommendation sent (to-integrator 1724).
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1216 passed (B branch). Throwaway merge main 8171eb1 + #15 (414aa1c) + #16 (13374a9) + #17 (6088d6b): flags off 1282 passed; `GV_TAIL` + `GV_DEMO_LIVE_FALLBACK` + `GV_FUZZY` on (set inside Python) 1282 passed. `eval.run_all` + `eval.gate` on that merge with DEMO=1 and all three flags on, no key: G4 gate 22 pass, 0 warn, 0 fail. Numbers are the same as flags off (11 calls / 20 questions, 0 personal fields, offline warm/synced 18/20). No eval question names a tail pair, so the eval does not exercise the tail send. The live fallback was not run (no key in the sandbox); it is covered only by unit tests with a stubbed cloud.
- **Inbox:** handled 20261108-1709-from-integrator-d041-single-tail-contract (no change needed). New: D-041, D-042, A-033 (sound-alikes, PR #17): nothing for B.
- **Next:** wait for PR #15 merge; re-run the flags-on eval on main after the merge; hold for G5 freeze.

### B-068 · 2026-11-08 17:21 · commit `e47dbdd` (PR #20) · PLAN v1.3.6

- **Change:** New long-tail partition `data/buckets/tail-v2.json`, built by `data/buckets/build_tail_v2.py` from D's `eval/fixtures/universe_v1.json`. It has the same 8376 keys as tail-v1, in 1047 buckets of 8. Only the grouping is new. Keys are tiered first by how many parts (drug or lab band) are missing from D's universe, then by the product of each part's summed synthetic priors, and each family is cut into consecutive groups of 8. Ties are broken by a seeded shuffle. `core/decoys.TAIL_VERSION = "tail-v2"`, and the router's cover tick now uses `TAIL_VERSION` instead of a hardcoded "tail-v1". tail-v1.json stays in the repo and still loads (I5: a new partition is a new version file).
- **Why:** D-017 / to-B 1717. On tail-v1 the statistical attacker won 59% of the time (51% with unseen drugs at the median), because a seeded shuffle put one common-drug pair among seven rare ones. The D-040 part 2 text asks for "grouped by frequency tier where priors exist".
- **Result (D's `eval.adaptive.attack_partition`, 500 patients, 3 asks):** with unseen drugs at the smallest prior, statistical 0.59 -> 0.15 (ceiling 0.58 -> 0.129). With unseen at the median, 0.51 -> 0.13. Repeat-ask about 0.11 (1 in 8 expected). Seeds 7, 11 and 23 all fall between 0.12 and 0.16. Core is 22%, so the tail is now better than the core on this attacker. Because the first tier is the unseen count, every bucket holds keys from one unseen class, and the ranking inside a bucket does not change with the value an attacker gives unseen drugs.
- **Class:** Advances
- **Plan:** advances D-040 part 2; I5, P6.5 kept; I3 unchanged (same keys, same topic texts, aliasing unchanged)
- **Contract impact:** none (ledger bucket_id still `tail-NNNN`; ids now point at different groups, but nothing outside B stores them)
- **Affects:** D: `eval/adaptive.py` `TAIL_FILE` points at `tail-v1.json`. Point it at `tail-v2.json` (or read `core.decoys.TAIL_VERSION`) so E1 reports the shipped partition. C: none. A: none.
- **Demo impact:** none with GV_TAIL off (the default). With it on, a different set of 7 keys travels with a tail pair.
- **Tests:** `make test` exit 0, 1293 passed. New `tests/B/test_tail_v2.py`: tail-v2 is current, rebuilds byte-identically, holds exactly tail-v1's keys, all buckets have 8 keys, and the statistical attacker is <= 0.20 with ceiling < 0.15 under both unseen readings.
- **Inbox:** handled 20261108-1717-from-D-tail-finding. New LOG: D-017 (the finding), A-034 (suggest swap tests): nothing else for B.
- **Next:** after PR #20 merges, re-run the flags-on suite and eval on main. Hold for the 18:00 ON/OFF call and the G5 freeze.

### B-069 · 2026-11-08 17:30 · commit `cdb8ee2` (PR #20) · PLAN v1.3.6

- **Change:** No new B code. PR #20 rebased onto main 1e0d176 and re-pushed (head `cdb8ee2`, 2/2 checks green, mergeable). Pre-18:00 rehearsal: a throwaway merge of main + #20 (cdb8ee2) + #18 (A, 46f5304) + #19 (I intent, c8671c7), tested with flags off and with flags on (flags set inside Python, other GV_* cleared).
- **Why:** BRIEF queue is done. The 18:00 ON/OFF call needs to know whether the open PRs work together under each flag set.
- **Result:** merges with no conflicts. Flags off: 1311 passed, 1 xfailed (A-035 hyphen xfail). `tests/B` with GV_INTENT + GV_TAIL: 571 passed. GV_TAIL + GV_FUZZY + GV_DEMO_LIVE_FALLBACK: 1310 passed, 1 failed. All four flags: 1308 passed, 3 failed. None of the failures are in B code or tests:
  1. `tests/I/test_intent.py::test_flag_off_by_default`: fails whenever GV_INTENT=1 is exported. This is expected from the test's own premise.
  2. `tests/I/test_intent.py::test_drug_typos_are_never_repaired_here`: fails with GV_FUZZY=1. `core/intent.py:271` repairs `simvastain` -> `simvastatin` through A's `suggest()` on purpose, but the test does not pin GV_FUZZY off.
  3. `tests/C/test_adaptive.py::test_ask_routes_the_corrected_question`: fails with GV_INTENT=1. The route gets the canonical "Does clopidogrel interact with aspirin?" instead of the fuzzy-swapped original, and the test does not pin GV_INTENT off.
  All three are test-isolation gaps. None of them is a router or I4 behaviour bug.
- **Class:** Advances
- **Plan:** advances D-040 (parts 1-3 + intent), G5 readiness; no invariant touched
- **Contract impact:** none
- **Affects:** I: items 1-2 in #19 (monkeypatch the flags in those tests). C: item 3 (`monkeypatch.delenv("GV_INTENT")` in test_adaptive). Messages sent. A, D: nothing.
- **Demo impact:** none. These are test-only failures, and they happen only when the flags are exported to the whole suite.
- **Tests:** `make test` on B branch exit 0, 1293 passed. Merge results as above. Eval not re-run (PR #20 not merged yet).
- **Inbox:** no new messages. New LOG: A-035 (nothing for B). No new DECISIONS (still D-042).
- **Next:** after PR #20 merges, run the flags-on suite and eval on main. Hold for 18:00 ON/OFF and G5 freeze.

### B-070 · 2026-11-08 17:40 · commit `cdb8ee2` (PR #20) · PLAN v1.3.6

- **Change:** No new B code. Main moved only by coord commits since B-069 (ccc6c51, 0f06609, 916c62a, b547728, 6ed0e77). Branch rebased locally (head 206fc04, same code as cdb8ee2) and re-tested. PR #20 left at `cdb8ee2` (2/2 checks green), no re-push.
- **Why:** BRIEF queue is done. PR #20 is with Gabe (integrator escalation 1722: hold unless GV_TAIL goes ON). The 18:00 ON/OFF call is still open.
- **Class:** Advances
- **Plan:** G5 readiness; no invariant touched
- **Contract impact:** none
- **Affects:** nobody. No messages sent.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1293 passed.
- **Inbox:** no new messages for B. New LOG: A-035 status, D-018 (presentation script, PR #21): nothing for B. No new DECISIONS (still D-042). Integrator pass 0f06609 escalated B's flag rec (all OFF) and PR #20 to Gabe.
- **Next:** if Gabe turns GV_TAIL ON, #20 merges first, then B re-runs the flags-on suite + eval on main. Otherwise hold for G5 freeze.

### B-071 · 2026-11-08 17:29 · commit `cdb8ee2` (PR #20) · PLAN v1.3.6

- **Change:** No new B code. Main moved only by coord commits since B-070 (50935df B report, 9116895 A-035 status). Branch rebased locally (head 6c132d4, no code diff vs cdb8ee2) and re-tested. PR #20 left at `cdb8ee2` (2/2 checks green), no re-push.
- **Why:** BRIEF queue is done. PR #20 still waits on Gabe's 18:00 GV_TAIL ON/OFF call.
- **Class:** Advances
- **Plan:** G5 readiness; no invariant touched
- **Contract impact:** none
- **Affects:** nobody. No messages sent.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1293 passed.
- **Inbox:** no new messages for B. New LOG/STATUS: A-035 status update (nothing for B). No new DECISIONS (still D-042), no new proposals.
- **Next:** if GV_TAIL goes ON, #20 merges first, then B re-runs the flags-on suite + eval on main. Otherwise hold for G5 freeze.

### B-072 · 2026-11-08 17:31 · commit `cdb8ee2` (PR #20) · PLAN v1.3.6

- **Change:** No new B code. Main moved only by one coord commit since B-071 (0c8e8f9 A-035 status). Branch rebased locally (head 8600698, no code diff vs cdb8ee2) and re-tested. PR #20 left at `cdb8ee2` (2/2 checks green), no re-push.
- **Why:** BRIEF queue is done. PR #20 still waits on Gabe's 18:00 GV_TAIL ON/OFF call.
- **Class:** Advances
- **Plan:** G5 readiness; no invariant touched
- **Contract impact:** none
- **Affects:** nobody. No messages sent.
- **Demo impact:** none
- **Tests:** `make test` exit 0, 1293 passed.
- **Inbox:** no new messages for B. No new LOG entries needing action, no new DECISIONS (still D-042), no new proposals.
- **Next:** if GV_TAIL goes ON, #20 merges first, then B re-runs the flags-on suite + eval on main. Otherwise hold for G5 freeze.

### B-073 · 2026-11-08 17:34 · commit `f4891e2` (PR #20) · PLAN v1.3.6

- **Change:** New `tests/B/test_single_reach.py` (tests only). Pins that with GV_TAIL on, every key A's rules can produce (`rules.all_keys()`, 44 keys) is in core or tail, or is an allergy key (16) that `generalize()` drops; and that real questions with Alex's flags give `single_candidates == []` with nothing recorded. PR #20 rebased onto main 53f5377 and pushed (head f4891e2).
- **Why:** C's FYI (C-031): the D-041 consent box never appeared. That is by design: tail-v1/v2 holds every drug pair over A's vocabulary plus one drug-lab key per ingredient/lab, so `single_candidates` is only a safety net for keys A may add later. The test fails and names the key if a cloud key ever lands outside both partitions.
- **Class:** Advances
- **Plan:** D-040 part 2, D-041, I4, I5; no invariant touched
- **Contract impact:** none
- **Affects:** C (answer to the FYI, no change needed; to show the box in a UI test, pass a stub flag with a needs_cloud key outside both partitions). A (a new needs_cloud key must join a partition, or this test turns red).
- **Demo impact:** none (consent box does not appear in the S-beats with today's data)
- **Tests:** `make test` exit 0, 1300 passed.
- **Inbox:** handled 20261108-1731-from-C-flag-isolation-fixed.md (B-069 isolation gap closed in PR #22, thanks) and 20261108-1733-from-D-tail-v2-done.md (E1 follows TAIL_VERSION, nothing more for B). No new DECISIONS (still D-042), no new proposals.
- **Next:** if GV_TAIL goes ON, #20 merges first, then B re-runs the flags-on suite + eval on main. Otherwise hold for G5 freeze.

### B-074 · 2026-11-08 17:38 · commit `f4891e2` (PR #20) · PLAN v1.3.6

- **Change:** No new B code. Main moved only by coord commits (1c51c94, e9e3b9d A-036; 2dffacf integrator escalation). Branch rebased locally (head de8dc5d, no code diff vs f4891e2) and re-tested. PR #20 left at `f4891e2` (green), no re-push. Merge rehearsal for the integrator's suggested order: main 2dffacf + #22 (b991470) + #18 (e34e618) + #21 (c6e05f4) + #20 (f4891e2) + #23 (5398fad) + #19 (ecbf7c6). No conflicts. `make test` exit 0, 1335 passed with DEMO unset (as CI runs), with DEMO=1, and with DEMO=1 plus GV_TAIL, GV_DEMO_LIVE_FALLBACK, GV_FUZZY, GV_INTENT and GV_DIRECT all exported. The #19 flag-isolation fails from B-069 are gone.
- **Finding (integrator-owned, test-only):** `tests/I/test_direct.py:10` and `tests/I/test_intent.py:10` do `os.environ.setdefault("DEMO", "1")`. If a shell exports `DEMO=0`, as B's did, setdefault keeps 0 and the cloud stays cold. Then 3 tests in test_direct.py fail with a correct no_data answer ("no data on clopidogrel with pantoprazole"). Main + #19 alone fails the same way. This is not a router bug. Fix: set DEMO=1 with monkeypatch or mock.patch.dict inside the test or fixture, not setdefault at import time.
- **Why:** Gabe has five or six merges to make before G5. A rehearsal of the full set, including #21's tail eval against #20's tail-v2, shows the order is safe.
- **Class:** Advances
- **Plan:** G5 readiness; D-040, D-041; no invariant touched
- **Contract impact:** none
- **Affects:** integrator (the DEMO=0 finding on #19; the rehearsal result for the merge order). No one else.
- **Demo impact:** none (the demo machine runs DEMO=1, which is green)
- **Tests:** branch `make test` exit 0, 1300 passed. Rehearsal merge as above.
- **Inbox:** handled 20261108-1735-from-integrator-pr19-isolation-ack.md (nothing needed from B). No new DECISIONS (still D-042), no new proposals.
- **Next:** if GV_TAIL goes ON, #20 merges first, then B re-runs the flags-on suite + eval on main. Otherwise hold for G5 freeze.
