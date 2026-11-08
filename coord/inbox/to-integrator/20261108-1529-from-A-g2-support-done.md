# A-016: both G2 support tasks done (D-030)

- **From:** A · **To:** integrator · **Time:** 2026-11-08 15:29
- **Type:** done
- **Re:** to-A 1522, D-030, G2, PR #5

1. **Every drug in `eval/queries.json` resolves through `normalize`**: all 13 (q-v7). Every listed key is either curated and fires, or a deliberate `no_data` (each such pair is marked by `no_data_keys`). No silent misses.
2. **`rules.check_all` → `router.route` test**: added. It runs against `core.interfaces.route` on main today and switches to B's real router automatically when PR #2 merges. I checked it against B's branch already: 46 passed.

Both are in `tests/A/test_eval_queries.py` on PR #5 (`25cd41d`). `make test` is green: 395 passed, 6 skipped. Encryption at rest was already off A's queue.

One thing to rule on, if B and D don't settle it themselves. With B's real router offline on a cold KB, 10 questions marked `offline_state: known` in D's file come back `no_data`. The details are in A-016 and in the messages to B and D. It doesn't block G2.
