# D-041: single send and tail label ruled, no contract type change

- **From:** integrator (Gabe) · **To:** B · **Time:** 2026-11-08 17:09
- **Type:** ruling
- **Re:** to-integrator/20261108-1656-from-B-adaptive-questions-ready.md, D-040, D-041, PLAN v1.3.6

- Your question: the `tail` ledger label and the "single, not hidden" path do **not** need a contract change. You keep `LedgerEntry.kind` as is and mark them by `bucket_id` (`tail-NNNN`, `single`), as PR #15 does. CONTRACTS now writes that convention down.
- `router.single_candidates(question, flags) -> list[str]` and `router.send_single(key) -> Answer` are now in CONTRACTS as additive, with flag-off stubs in `core/interfaces.py` (`[]` and `no_data` with `sent_to_cloud=False`).
- Nothing to change on your side. Keep those signatures and the `bucket_id` values fixed until freeze.
- PR #15 merge has gone to Gabe (to-human 1709).
