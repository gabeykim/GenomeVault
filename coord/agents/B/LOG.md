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
