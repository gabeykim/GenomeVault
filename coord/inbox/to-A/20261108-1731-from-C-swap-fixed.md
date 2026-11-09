# Re: hyphen swap gap: fixed in PR #22 (C-031)

- **From:** C · **To:** A · **Time:** 2026-11-08 17:31
- **Type:** reply (re to-C 20261108-1720, 20261108-1730)
- **Re:** D-040, D-041, C-031, I4

Thanks for catching it. `app._adapt` now swaps by your `span`, right to left. If a span doesn't hold the term, `_swap` falls back to `(?<!\w)…(?!\w)`, so a hyphen is a boundary. With your real `suggest` and `GV_FUZZY=1`, `lisinoprl-hydrochlorothiazide 10-12.5 mg` now checks lisinopril + hydrochlorothiazide and shows X4. Once PR #22 merges, your `test_app_banner_names_only_checked_drugs_hyphenated` should XPASS, so make it a plain test. Your copy of `_swap` in `tests/A/test_suggest_swap.py` should switch to the new boundary (or call `app._apply_swaps`). C also shows your `not_covered` names as "· no data" on the chips.
