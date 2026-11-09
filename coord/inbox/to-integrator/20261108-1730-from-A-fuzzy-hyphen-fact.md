# Fact for the 18:00 GV_FUZZY call: one hyphen case hides a flag

- **From:** A · **To:** integrator · **Time:** 2026-11-08 17:30
- **Type:** information
- **Re:** D-040 parts 1 and 4, D-041, I4; A-035, PR #18 (tests only)

On main with `GV_FUZZY=1`, plain typos work end to end through `/api/check`: Simvastatn, Atorvastatn and Warfrin® are assumed, and the check runs on the meant drug. D measured 20/20 with 0 silent wrong substitutions. There is one gap, in C's `app._swap`. A typo inside a hyphenated combo (`lisinoprl-hydrochlorothiazide`) shows "assuming lisinopril", but the check runs on hydrochlorothiazide only, so X4 is missed. I've asked C to fix it (to-C 1730; it's a one-line change). If it isn't fixed by 18:00, that's a reason to keep GV_FUZZY OFF, or to accept the risk because the demo script doesn't type hyphenated combos. PR #18 is tests only, and the case is a non-strict xfail there.
