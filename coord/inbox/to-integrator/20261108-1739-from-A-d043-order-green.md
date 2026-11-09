# D-043 merge order is green with flags on and off. #18 needs no edit.

- **From:** A · **To:** integrator (Gabe, Dhiaa) · **Time:** 2026-11-08 17:39
- **Type:** info
- **Re:** D-043, to-A 1745, A-037

I rehearsed your order with merge commits in a throwaway worktree: main `62b0e39` → #22 `b991470` → #20 `f4891e2` → #18 `e34e618` → #21 `c6e05f4` → #19 `ecbf7c6` → #23 `5398fad`. All six merged clean.

- `make test` with flags unset: exit 0, 1335 passed.
- `make test` with `GV_FUZZY GV_TAIL GV_DEMO_LIVE_FALLBACK GV_INTENT GV_DIRECT` all set to 1: exit 0, 1335 passed.
- A's hyphen tests are plain passes once #22 is in (no xfail, no skip).

I did not run `scripts/demo_proof.py`. That is your gate on the demo machine.

PR #18 stays at `e34e618`. A pushes nothing more unless something is demo-critical.
