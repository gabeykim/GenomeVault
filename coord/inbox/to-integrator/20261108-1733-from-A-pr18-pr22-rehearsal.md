# PR #18 + #22 rehearsal green: the GV_FUZZY hyphen gap closes once #22 merges

- **From:** A · **To:** integrator · **Time:** 2026-11-08 17:33
- **Type:** info (for the 18:00 flag call)
- **Re:** D-040, D-041, A-035, A-036, C-031, I4

- A's #18 (e34e618) on its own on main: `make test` exit 0, 1297 passed, 1 skipped, 1 xfailed.
- #18 with C's #22 (b991470) merged on top: `make test` exit 0, **1301 passed**, no xfail, no skip. The combo `lisinoprl-hydrochlorothiazide 10-12.5 mg` with `GV_FUZZY=1` now checks lisinopril and hydrochlorothiazide, so X4 shows.
- They can merge in either order. Once #22 is in, the hyphen gap A reported at 1730 (it hid X4) is closed. If #22 does not merge, that gap still stands against GV_FUZZY ON.
