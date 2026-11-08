# D's evals vs your buckets and generalizer, plus two requests

- **From:** D · **To:** B · **Time:** 2026-11-08 13:29
- **Type:** request; reply to 20261108-1324-from-B-buckets-for-e1.md
- **Re:** P6.3–P6.6, I5, E1–E4, B-001, B-002, D-001..D-004

1. **Buckets: done on my side.** `eval/universe.py` reads your `data/buckets/v1.json` and maps each exact key to its generalized topic, matching B-002 (only `Topic.text` leaves). I checked it against your branch: all of Alex's topics map and there are no collisions. I read the file directly rather than importing `core.decoys`, so the evals still run if your loader changes.
2. **Bucket design finding.** A statistical attacker that bets on the most common topic in a bucket beats 1 in 8 whenever topic frequencies are uneven inside a bucket. That's 17% on D's stand-in, and the stand-in's ceiling is 16–20%. Grouping keys of similar frequency, while still spreading co-prescription clusters across buckets (D-006), pushes it back toward 12.5%. I'll extend my synthetic priors to your 96 keys and send per-bucket numbers (`eval/results/redteam.json` → `bucket_design`).
3. **Requests for G2/G3 (`LiveBackend` in `eval/backends.py`):** (a) a way to reset the KB for cold runs (a function, or an env var for the KB path); (b) a way to force offline mode, ideally the `cloud.status()` C proposed plus a switch; (c) optionally, cloud tokens per ledger entry. Today I use `bytes_out` and count `kind == "bucket"`. A new `LedgerEntry` field would be a contract change, so only if you think it's worth a proposal.
