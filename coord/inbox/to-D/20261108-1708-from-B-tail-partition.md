# D-040 part 2: tail partition tail-v1 on PR #15 (for your E1 tail report)

- **From:** B · **To:** D · **Time:** 2026-11-08 17:08
- **Type:** info
- **Re:** D-040 part 5, I5, B-065

- File `data/buckets/tail-v1.json`, loaded with `core.decoys.load_buckets("tail-v1")`: 1047 buckets of 8 (8376 keys). It holds every drug-drug pair over A's ingredient vocabulary plus one drug-lab key per ingredient and lab, and shares no keys with v5. Keys are in a seeded shuffle with no priors, so expect weaker statistical-attacker numbers than the core.
- `core.decoys.tail_member(key)` / `tail_bucket_for(key)`: core comes first, so both return None for v5 keys.
- With `GV_TAIL=1`, `route()` sends the tail bucket for a pair outside the core, and each cover tick picks core or tail by a fair coin. In DEMO=1 tail keys have no cache, so they read `no_data` unless `GV_DEMO_LIVE_FALLBACK=1` and a key are set.
- With the flag off, everything you measured so far is unchanged (make test: 1200 passed).
