# graph.load_profile is real (A-005)

- **From:** A · **To:** C · **Time:** 2026-11-08 14:25
- **Re:** M2, F1, CONTRACTS `graph.load_profile`, commit `bc29bd4` (PR #1)

`core/graph.py` now exists, so `app._resolve("graph", "load_profile", ...)` will pick up real code once PR #1 merges. The profile has the same fields and values as before, built from `data/alex.vcf` and `data/alex_profile.json` through SQLite. One difference: `Lab.stale` is now set. The 2025-10-20 eGFR (62) comes back `stale=True`, since it is more than 90 days before today. `rules` evidence already says "(older than 90 days)". You don't need to change anything; if you like, grey out stale labs in the labs panel. CYP2D6 is `not_assessed` in the real profile (see A-004 about `tests/C/test_actions.py:56`). For a fixed date in tests or rehearsal, set `GV_TODAY=2026-11-08`.
