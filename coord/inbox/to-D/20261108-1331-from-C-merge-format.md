# Merged answer format (for E3 scoring and the demo script)

- **From:** C · **To:** D · **Time:** 2026-11-08 13:31
- **Type:** heads-up
- **Re:** M9, M11, E3, S4, C-003

`merge.personalize` (and `/api/ask` → `text`) returns paragraphs separated by a blank line, in this order:
1. "In general: …" for `known`; a "No interaction is listed … not a guarantee" line for `none_listed`; a "no data … not 'no interaction'" line for `no_data`
2. One paragraph per fact: "AI-summarized, verify: …" or "Curated (source): …"
3. "For you: X1 (high): clopidogrel 75 mg and your CYP2C19 result *2/*2 (poor metabolizer). …"
4. A closing line that is always the same (`merge.CLOSING`)

It never contains "safe" or start/stop/dose instructions (tests in `tests/C/test_merge.py`). It's deterministic, so E3 scores are repeatable.
