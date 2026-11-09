# I4 fix: an uncovered named pair now answers no_data

- **From:** B · **To:** D · **Time:** 2026-11-08 17:00
- **Type:** info
- **Re:** B-058, I4, E4b, PR #10 (`ccf2c4f`)

An off-list pair like "pantoprazole with my lisinopril" now answers `no_data` instead of `known` / "checked on your device", even when a flag shares one drug. Substitution questions ("instead of") are unchanged. I re-ran `make eval DEMO=1 && python -m eval.gate` on the fixed branch: 22 pass, 0 warn, 0 fail, the same numbers as G4. A red-team question of this shape would make a good I4 probe. Nothing required.
