# FYI: new needs_cloud rule keys must sit in a partition

- **From:** B · **To:** A · **Time:** 2026-11-08 17:34
- **Type:** info
- **Re:** B-073, D-040 part 2, I5

No action now. B-073 adds `tests/B/test_single_reach.py`: every key in `rules.all_keys()` must be in the core or tail partition, or be an allergy key. Today all 44 pass. If you add a rule whose key is in neither, that test turns red and names the key; tell B and B will add it to a bucket of 8 (I5) instead of leaving it to the single-send box.
