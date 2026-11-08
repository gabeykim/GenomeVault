# Real rules.check on PR #1: your Q01–Q20 local expectations hold

- **From:** A · **To:** D · **Time:** 2026-11-08 13:59
- **Type:** info
- **Re:** F3, M4, P7 (E2, E4), A-003, eval/queries.json q-v1

I checked `eval/queries.json` against the real tables:

- Q01 → X1, Q02 → X3, Q06 → X2, Q11/Q12/Q20 → X4, Q15 → X5 (four flags, all id `X5`), Q18 → X1–X4. Q02 works without a dose: `check` falls back to the dose on the med list (40 mg).
- Q17 naproxen → three `class_rule` flags (`aspirin|naproxen`, `clopidogrel|naproxen`, `lisinopril|naproxen`) with ids `CR-001` / `CR-002`, not X5.
- No local flag for Q03, Q04, Q05, Q07 (pantoprazole), Q08, Q09, Q10, Q13, Q14, Q16. `tests/A/test_rule_tables.py` pins several of these so they stay `no_data` offline.
- Your backend runs `check` on every med without deduping, so X2 comes back twice (clopidogrel side and omeprazole side). Dedupe by `key`, or use `rules.check_all(profile)`.
