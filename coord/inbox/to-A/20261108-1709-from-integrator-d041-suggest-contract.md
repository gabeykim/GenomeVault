# D-041: `normalize.suggest` is in CONTRACTS (additive)

- **From:** integrator (Gabe) · **To:** A · **Time:** 2026-11-08 17:09
- **Type:** ruling
- **Re:** to-integrator/20261108-1657-from-A-adaptive-part1-ready.md, 20261108-1706-from-A-pr17-ready.md, D-040, D-041, PLAN v1.3.6

- Your PR #17 shape is now the contract: `suggest(text) -> list[dict]` with keys `token`, `term`, `span`, `mode` (`assumed`|`ask`), `assumed`, `choices` (1–3), `not_covered`. `[]` unless `GV_FUZZY=1`. A stub returning `[]` is in `core/interfaces.py`.
- Nothing to change on your side. Please keep the shape fixed until freeze; any key change is now Alters.
- PR #17 merge has gone to Gabe with #14, #15, #16 (to-human 1709). Whether `GV_FUZZY` is ON is ruled at 18:00 per D-040.
