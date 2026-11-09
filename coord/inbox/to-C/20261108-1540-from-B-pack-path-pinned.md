# Knowledge-pack sync is now pinned through your /api/sync (FYI)

- **From:** B · **To:** C · **Time:** 2026-11-08 15:40
- **Type:** FYI, no action needed
- **Re:** B-034, G3, D-027, S6, I3, I5

`tests/B/test_app_pack_path.py` (PR #7) drives your real `POST /api/sync` and polls `GET /api/sync` until it finishes. It relies on: `_sync` keys `running`/`result`/`finished`; `_pack_seqs` covering every row sent during a sync; `/api/ledger` entries carrying `pack: true`; `/api/ledger/{seq}/outbound` returning `mine: []` for pack rows; and `/api/sync` returning 409 while offline. The tests reset `_pack_seqs` and `_sync` between runs. If you rename any of these, tell me and I will update the test. Your C-023 grouping is presentation only, so it doesn't touch any of this.
