# CYP2D6 is now not_assessed; optional DAPT info note

- **From:** A · **To:** C · **Time:** 2026-11-08 14:17
- **Type:** info (one test of yours will need a change)
- **Re:** D-021, P5 (v1.2), A-004

1. On PR #1 (`3ce9f6d`), `data/alex_profile.json` has CYP2D6 genotype `not_assessed` and phenotype `not_assessed` (D-021: not callable from SNP data). I asked the integrator to change `mocks/alex_profile.json` the same way. `tests/C/test_actions.py:56` asserts `"CYP2D6 *1/*1: normal metabolizer"` and will fail after that. Suggest you show it as "CYP2D6: not assessed" or leave the gene out.
2. `aspirin|clopidogrel` never produces a Flag. If you want the informational line from PLAN v1.2 P5, call `core.rules.expected_notes(drug, profile)` for one drug, or `core.rules.expected_notes_all(profile)` for the med list. Each returns a list of `{id, key, text, source}` dicts (Alex gets one, `EX-001`). Render it as info, not as a flag or warning, and don't say "safe" (I7). Before G1 merges, `getattr(rules, "expected_notes_all", lambda p: [])` keeps you safe.
3. Flags and keys are unchanged.
