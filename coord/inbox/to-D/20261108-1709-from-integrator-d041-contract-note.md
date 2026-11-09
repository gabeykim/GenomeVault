# D-041: D-040 interfaces in CONTRACTS (FYI for E1 tail / typo eval)

- **From:** integrator (Gabe) · **To:** D · **Time:** 2026-11-08 17:09
- **Type:** heads-up
- **Re:** D-040 part 5, D-041, PLAN v1.3.6

- `normalize.suggest`, `router.single_candidates` and `router.send_single` are in CONTRACTS (additive). Tail sends show in the ledger as `bucket_id` `tail-NNNN`, single sends as `bucket_id` `single`. Report E1 for the tail separately using these ids.
- PR #14 is still waiting on Gabe to merge (to-human 1709). Nothing for you to change.
