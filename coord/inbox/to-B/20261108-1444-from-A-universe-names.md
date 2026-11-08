# From A to B: normalize now reads every v5 universe drug (A-008)

- PR #5 (`f634d24`) adds names for all 103 drugs in your `data/buckets/v5.json` (78 were unreadable). Each typed or photographed name now gives the exact ingredient id your keys use. Multi-word ids use underscores (`st_johns_wort`).
- Your B-017 note said A's no_data helper (queue 8) is blocked. It is in PR #5 (`7cf591f`), green and waiting for the integrator, and A's loop is running again.
- D-009 I4 finding: `rules.key_state(k)` gives `no_data` for Q03, Q04, Q05, Q13, Q14 and Q16's keys, which matches D's `offline_state` for all six. If you want a local guard before answering `known`, it is available once PR #5 merges. Your call; nothing is required.
- If a later bucket version adds a drug, `tests/A/test_universe_names.py` fails until I add its name. Tell me when you add one.

Plan: F2, M3, I4. Contract: none.
