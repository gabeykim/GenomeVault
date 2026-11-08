# Integrator: encryption-at-rest rejected; refocus on G2 support (D-030)

- **From:** integrator (Gabe, acting through G2 per D-024) · **To:** A · **Time:** 2026-11-08 15:22
- **Type:** ruling + task
- **Re:** D-030, 20261108-1454-from-A-crypto-dependency, G2, eval/queries.json, CONTRACTS, M4

**Encryption at rest: rejected (D-030).** No new `cryptography` dependency before G2 — it would need an install on every agent machine mid-run, and "stored locally" already covers the privacy pitch. Please **remove encryption-at-rest from your queue** (the pitch stays "stored locally", not "encrypted at rest").

**Your time goes to G2 support instead:**
1. Make sure **every drug in `eval/queries.json` resolves through `normalize`** to either a curated exact key or a deliberate `no_data` case — no silent misses.
2. Add a **test that `rules.check_all` output feeds `router.route`** under the current contracts (the Flag list → Answer handoff), so the A→B path is pinned before G2.

This keeps the G2 end-to-end path (rules → router) solid. Thanks!
