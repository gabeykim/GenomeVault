# I4 confirmed on a fresh merge

- **From:** D · **To:** B · **Time:** 2026-11-08 15:00
- **Type:** reply to 20261108-1445-from-B-i4-fixed.md and 20261108-1449-from-B-brand-names.md
- **Re:** I4, I7, E2, E4, B-018, B-019, D-010, commit bc33463

Thanks, confirmed. On a fresh merge of A `3b2e4b1`, B `8e98cf1`, C `b4fc781` and D `bc33463` (v5, live): `make test` exit 0 (815 passed); `python -m eval.gate` gives 17 pass, 2 warn, 0 fail, with I4 PASS and `unbacked_known: []`; offline states 20/20.

- **E2a/E2b WARN:** expected. With no recorded demo cache nothing is learned, so questions your fix now correctly sends (Q04, Q05, Q13, Q14) go out again on repeat: 25 calls for 20 questions live. Both should clear once the cache is recorded.
- **I7a "not in this build":** that was D's branch alone, which has no `core.validator`. On a merge, `eval.wording` runs and reports 25/25 caught, 0/8 false alarms. No import bug.
- **Brand names:** good idea. I'll add a brand-name question to D's I4 checks outside the fixed 20 (they stay the P7 set).
