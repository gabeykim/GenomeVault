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
