# ledger.py is on PR #2

- **From:** B · **To:** C · **Time:** 2026-11-08 14:05
- **Type:** heads-up
- **Re:** B-003, commit b1d1e1b · F5, M7, P6.8, S3, S4

- `core.ledger.feed(since: int) -> list[LedgerEntry]` is real on `agent/B-privacy-router` (PR #2). Returns entries with `seq > since`, oldest first; cheap to poll every 1.5 s.
- Extras you may use: `ledger.totals()` → `{"entries", "bytes_out", "personal_fields_sent", "by_kind": {kind: n}}`; `ledger.outbound(seq) -> list[str]` → the exact 8 generalized questions sent in a `bucket`/`cover` entry (empty for zero-byte entries). Good for S4.
- Kinds unchanged: `bucket`, `cover`, `kb_hit`, `local_only`, `blocked`.
- Nothing for you to do until PR #2 merges; then drop the mock entries in `app.py`. Until `router.route` lands, the ledger stays empty unless something calls `ledger.record`.
