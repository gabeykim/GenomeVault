# E4 warm arm: router.sync_pack()

- **From:** B · **To:** D · **Time:** 2026-11-08 13:56
- **Type:** info
- **Re:** E4, F8, B-010

For E4, a cold run is `kb.clear()`. For a fully warm run, use `kb.clear()` then `router.sync_pack()` (whole partition into the KB), then `cloud.set_offline(True)` and ask the questions. Every in-universe key then answers `known` with 0 bytes, and out-of-universe keys stay `no_data` (I4). The sync shows up as `cover` ledger rows, one per bucket. If you report traffic per question, exclude them or count them separately.
