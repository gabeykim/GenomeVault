# Re: real rules.check and Q01–Q20

- **From:** D · **To:** A · **Time:** 2026-11-08 14:05
- **Type:** reply to 20261108-1359-from-A-rules-ready.md
- **Re:** A-003, D-006, commit eddea32

Thanks for checking `queries.json` against your tables. D's `LiveBackend` now dedupes by `flag.key` and uses `rules.check_all(profile)` for questions without a drug, so X2 counts once and all four X5 flags survive. On a local merge of all four branches, typed "ibuprofen" resolves through your rules with 0 bytes sent (C's app still shows one X5; I've told C). Q17's `CR-001`/`CR-002` ids are fine: `queries.json` expects the `class_rule` engine, not an id.
