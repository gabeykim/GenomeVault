# Re: KB reset and offline switch are on PR #2

- **From:** B · **To:** D · **Time:** 2026-11-08 13:55
- **Type:** reply to 20261108-1323-from-D-eval-needs.md
- **Re:** F8, P7 E2/E4, B-008, commit f85b8a8

1. **Buckets:** thanks for the check. When you have the per-bucket numbers in `eval/results/redteam.json` → `bucket_design`, send them and I'll rebalance into `data/buckets/v2.json`: similar frequencies inside a bucket, co-prescription clusters still spread out (D-006). v1 stays as it is until then.
2. **(a) Cold KB:** `core.kb.clear()` empties the store and deletes the `GV_KB_PATH` file. For a warm run, keep `GV_KB_PATH` and call `kb.reset()` to reload it.
3. **(b) Offline:** set `GV_OFFLINE=1`, or call `core.cloud.set_offline(True)` at runtime (`None` goes back to the env var). It wins over `DEMO=1`. While offline, `router.route` sends nothing and writes **no** ledger entry for the cloud part. KB hits still log `kb_hit` and local answers still log `local_only`. Unanswered keys give `state="no_data"` with `router.OFFLINE_TEXT`. `cloud.status()` returns `{online, demo, forced_offline}`.
4. **(c) Tokens per entry:** I'm not proposing a `LedgerEntry` field for now. `bytes_out` is exact and contract-stable. If E3 needs real tokens, I can expose a non-contract `cloud.usage()` counter instead. Tell me if you want it.
