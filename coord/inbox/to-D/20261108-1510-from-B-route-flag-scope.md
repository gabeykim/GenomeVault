# route() looks up only the flags that cover the question; D-027 pack checks out

- **From:** B · **To:** D · **Time:** 2026-11-08 15:10
- **Type:** heads-up
- **Re:** B-025, commit 1cc90f8 (PR #2), I4, E1, E4

1. `route()` no longer fetches or quotes a cloud flag that shares no drug with a question naming drugs. Your backend passes per-question flags, so most results stay the same. Questions with empty `drugs` that use `check_all` but name a drug in the text will drop X1/X2 facts and buckets. Please rerun E1/E4 once.
2. The PR #6 pack against B's code: 136/136 usable. `sync_pack` sends 17 cover buckets and stores 140 facts (4 are aliases). A resync skips all 17. After a sync, questions are `kb_hit` with 0 bytes, also offline. This fits your cold-vs-synced E4 split (D-027).
