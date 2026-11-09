# D-041: the D-040 shapes you read are now in CONTRACTS

- **From:** integrator (Gabe) · **To:** C · **Time:** 2026-11-08 17:09
- **Type:** ruling / heads-up
- **Re:** to-integrator/20261108-1659-from-C-pr16-ask-input-fix.md, 20261108-1708-from-C-d040-part4.md, D-040, D-041, PLAN v1.3.6

- `normalize.suggest` (A's PR #17 keys, including `term`, `assumed`, `not_covered`), `router.single_candidates` and `router.send_single` (B's PR #15) are in CONTRACTS, with flag-off stubs in `core/interfaces.py`.
- Ledger labels: map `bucket_id` `single` → "Single question sent, not hidden" and `tail-NNNN` → "Tail group of 8 sent". `LedgerEntry.kind` is unchanged.
- Nothing for you to change, assuming PR #16 already reads these keys. PR #16 (with the C-029 Ask-click fix) has gone to Gabe to merge, along with #14, #15 and #17 (to-human 1709). Run your end-to-end test once A's and B's PRs land.
