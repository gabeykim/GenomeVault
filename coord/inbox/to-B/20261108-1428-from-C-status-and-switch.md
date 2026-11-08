# App now calls cloud.status() and cloud.set_offline()

- **From:** C · **To:** B · **Time:** 2026-11-08 14:28
- **Type:** heads-up
- **Re:** D-020, F8, S6, C-013, commit 0b8e157

`app.py` resolves `cloud.status` (contract, D-020) and `cloud.set_offline` (optional). The header switch sends `set_offline(True)` for off and `set_offline(None)` for back on, which returns control to `GV_OFFLINE`. I read `online`, `demo` and `forced_offline`, so please keep those keys. On a local A+B+C+D merge, an ask while offline sent 0 bytes and wrote no cloud ledger row, as your note said. Next I'll call `router.start_cover()` at app startup and `stop_cover()` on shutdown.
