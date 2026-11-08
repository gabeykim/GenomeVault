# How the app uses ledger.feed and route

- **From:** C · **To:** B · **Time:** 2026-11-08 13:10
- **Type:** heads-up
- **Re:** F5, M7, M5, C-001, commit c8a7839

- The UI polls `ledger.feed(since)` every 1.5 s and computes totals from `feed(0)`, so feed should be cheap.
- Once `core/ledger.py` exists, app.py stops writing mock entries; B's router writes every entry, including `local_only` / `kb_hit`.
- `/api/ask` calls `route(question, flags)` with all current flags for the meds list.
- The UI labels each kind: `local_only`, `kb_hit`, `bucket`, `cover`, `blocked`. Tell me if you add another.
