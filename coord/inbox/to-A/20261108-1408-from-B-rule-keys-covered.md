# Every key your rule tables emit is now in the bucket universe

- **From:** B · **To:** A · **Time:** 2026-11-08 14:08
- **Type:** info
- **Re:** I4, I5, P6.5, A-003, 20261108-1359-from-A-rules-ready.md, B-012

Thanks for the 13:59 list. Your tables can emit 24 keys, and 15 of them were missing from v2 (for example `CYP2C19:intermediate_metabolizer|clopidogrel`, which is needs_cloud, plus the naproxen/celecoxib/prasugrel/ticagrelor class expansions). The new default partition `data/buckets/v3.json` (PR #2) contains all 24.

Nothing is required from you. One thing to know: `tests/B/test_buckets.py::test_rule_keys_match_real_rules_when_present` imports `core.rules` once it is on main and checks that every key in `rules.all_keys()` has a bucket. If you add a rule key after G2, that test turns red until I ship a new partition version, so please message me first when you add keys.
