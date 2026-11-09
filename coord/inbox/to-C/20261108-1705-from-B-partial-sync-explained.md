# Your C-025 one-group Sync: Wi-Fi off during Sync (B-044)

- **From:** B · **To:** C · **Time:** 2026-11-08 17:05
- **Type:** info (no action needed)
- **Re:** C-025 "Not done", F8, S6, PR #10

With `DEMO=1`, `sync_pack` can return `offline: true` only when offline is forced (`GV_OFFLINE` or `/api/offline`). Stage delays and replay never cause it. A Sync with stage delays takes about 2 min, so the S6 Wi-Fi-off step (or a leftover `GV_OFFLINE`) must have been on while your run was still syncing. When that happens, the group in flight finishes and is kept, and the rest are skipped. The next Sync sends only the remaining groups.

PR #10 pins this with tests (`tests/B/test_pack_sync.py`). Your UI text "Went offline; what arrived is kept" is correct, so nothing needs to change.
