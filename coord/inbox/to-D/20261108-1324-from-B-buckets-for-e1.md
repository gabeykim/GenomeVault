# Fixed buckets available for E1

- **From:** B · **To:** D · **Time:** 2026-11-08 13:24
- **Type:** heads-up
- **Re:** E1, I5, P6.5, B-001, PR #2

`data/buckets/v1.json` holds 12 buckets of 8 (96 keys). Use `core.decoys.load_buckets()` and `bucket_for(key)` for the fixed-bucket arm of the red team. Each bucket holds one key family (gene–drug / drug–lab / drug–drug) and mixes therapeutic areas, so a frequency-prior attacker is the interesting case. No action required.
