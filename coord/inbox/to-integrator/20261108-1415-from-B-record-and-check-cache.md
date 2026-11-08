# Demo cache: record (restartable) + check (I7, I8)

- **From:** B · **To:** integrator · **Time:** 2026-11-08 14:15
- **Re:** B-013, D-006 (S4/S6 blocked on empty `mocks/cloud_cache/`), my 13:50 message, I7, I8

PR #2 now has two tools you can use when recording the demo cache (`mocks/` is yours):

1. `ANTHROPIC_API_KEY=… python -m core.cloud record mocks/cloud_cache` makes 136 live calls, one file per bucket, b01–b17. If it dies partway, run the same command again: it skips buckets already complete.
2. `python -m core.cloud check`: offline only. It lists missing keys, answers that break I7 (says "safe", or gives a start/stop/change instruction), and keys outside the partition. Exit 0 = all 136 usable.

Answers rejected for I7 are dropped at replay and read as `no_data`, so they are never shown. Re-record those keys or reword them by hand (keep them general, no personal data), then run `check` again until it exits 0. Run this after merging PR #2, because the cache must match the v3 partition.
