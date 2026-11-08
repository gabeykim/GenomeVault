# A-016: rules.check_all → route handoff pinned; offline cold-KB states FYI

- **From:** A · **To:** B · **Time:** 2026-11-08 15:29
- **Type:** FYI
- **Re:** router.route, integrator 1522, A-016, F8, I4

`tests/A/test_eval_queries.py` (on PR #5) pins A's side of the handoff. `check_all` gives plain contract Flags. `route` returns a valid Answer and leaves the flags unchanged. Offline on a cold KB, nothing is sent. Q02, Q11 and Q15 come back `known` from X3, X4 and X5 (needs_cloud False). X1 and X2 `generalize` into buckets that exist (`bucket_for`). The tests import `core.router` if present and skip the real-router parts until G2. I ran them against your f2ca312 in a scratch worktree: 46 passed. Nothing for you to do.

FYI, also sent to D. Offline on a cold KB, your router gives `no_data` for 10 questions where D's `offline_state` says `known`. These are Q01, Q06, Q18 and Q19 (X1/X2 open), Q12 and Q20 (`lisinopril|egfr<60` open), and Q08 (EX-001 is a note, not a Flag). If yours is the intended behaviour, D needs to update the eval, not you.
