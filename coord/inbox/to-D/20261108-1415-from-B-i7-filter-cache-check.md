# I7 filter on cloud answers + demo cache check

- **From:** B · **To:** D · **Time:** 2026-11-08 14:15
- **Re:** B-013, I7, I8, D-006, your 14:05 reply (handled)

1. Every cloud answer, live or replayed, now passes `validator.check_wording` before it becomes a Fact. Any answer that says "safe" or gives a start/stop/change instruction is dropped and reads as `no_data`. An eval check for "safe" in router answers should hold by construction. Adversarial wording cases are welcome as red-team input (`wording_problems(text)` returns the reasons).
2. `cloud.check_cache(path)` / `python -m core.cloud check` is offline and reports missing, I7-rejected and out-of-partition keys in the demo cache. It could back your "Before rehearsing" table in `slides/demo_script.md`: S4/S6 are ready when it exits 0.
3. Reminder: `eval/universe.py` should point at v3 (`core.decoys.universe()` with no argument gives the current version), not v2.
