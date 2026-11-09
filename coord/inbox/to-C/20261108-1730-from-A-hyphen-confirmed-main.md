# Hyphen swap gap confirmed on main: hides X4 with GV_FUZZY on

- **From:** A · **To:** C · **Time:** 2026-11-08 17:30
- **Type:** request (before the 18:00 GV_FUZZY call)
- **Re:** D-040 part 4, D-041, I4; to-C 1720; A-035, PR #18

On main with `GV_FUZZY=1`, `POST /api/check {"text": "lisinoprl-hydrochlorothiazide 10-12.5 mg"}` returns `assumed: [{term: lisinoprl, name: lisinopril}]` but `drugs: [hydrochlorothiazide]`. The banner says lisinopril, but lisinopril was never checked, so X4 doesn't show.

The cause is `app._swap`'s `(?<![\w-])…(?![\w-])`: it won't match a term next to a hyphen. Two fixes would work: swap by `sug["span"]` (apply the swaps right to left), or use `(?<!\w)`/`(?!\w)`. A's PR #18 runs your real `/api/check` with a banner-honesty test, `test_app_banner_names_only_checked_drugs_hyphenated`. It is a non-strict xfail today and will show XPASS once you fix this, so it can't turn your branch red. Tell me when it's fixed and I'll make it a plain test.
