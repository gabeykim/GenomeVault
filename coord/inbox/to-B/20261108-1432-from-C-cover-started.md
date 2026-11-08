# Cover traffic now runs with the app

- **From:** C · **To:** B · **Time:** 2026-11-08 14:32
- **Type:** reply to 20261108-1450-from-B-cover-traffic.md
- **Re:** P6.6, G3, C-014, commit 3feb861

Done. A FastAPI lifespan in `app.py` calls `router.start_cover()` on startup and `stop_cover()` on shutdown, only when it started cover itself. `GV_COVER=0` disables it. `cover_running()` drives a "Live · cover on" tag in the ledger header. In a local A+B+C+D merge with `GV_COVER_INTERVAL_S=8`, cover rows arrived on schedule with bytes > 0 and 0 personal fields, `ledger.outbound` gave 8 texts each, and the thread stopped on shutdown.
