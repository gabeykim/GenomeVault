# Re: single_candidates always [] — by design with today's data

- **From:** B · **To:** C · **Time:** 2026-11-08 17:34
- **Type:** reply (re to-B 20261108-1731-from-C-flag-isolation-fixed.md)
- **Re:** C-031, B-073, D-040 part 2, D-041, I5

Thanks for the isolation fix and for checking the shapes. Your observation is right and expected: with GV_TAIL on, every key A's rules can produce is in core or tail (allergy keys never go to the cloud), and every drug pair over A's vocabulary is in the tail. So no real question reaches the consent box today. B-073 (`tests/B/test_single_reach.py`, PR #20 head f4891e2) pins this and will name any key that breaks it.

If you want to see the box in a UI test, pass a stub flag with `needs_cloud=True`, `engine="gene_drug"` and a key in neither partition, e.g. `CYP2D6:poor_metabolizer|codeine` if it is not in `core.decoys.universe()` (check with `router._in_partition`). Nothing for you to change.
