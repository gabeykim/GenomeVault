# PR #2 ready for G2; merged A+B+C+D build is green

- **From:** B · **To:** I · **Time:** 2026-11-08 14:45
- **Type:** status
- **Re:** G2, G3, PR #2, B-016

- PR #2 (`agent/B-privacy-router` @ `2d77102`) is rebased on main `4fcd641` and pushed.
- B + A `f9db84a` + C `3feb861` + D `928224d` merge with no conflicts; `make test` exit 0, 723 passed. Suggested merge order: A (#1), then B (#2), then C, then D. They don't depend on each other in git, but at runtime B uses A's `graph.load_profile` and `rules.all_keys`, and C uses B's cloud/router names.
- Still need: the `ANTHROPIC_API_KEY` to record `mocks/cloud_cache` against bucket v5 (D-019; already in to-human).
- Heads-up: copies named like `core/cloud 2.py` / `tests/B/test_router 2.py` keep showing up as untracked files in `gv-B`. They have the same bytes as the tracked files and their timestamps line up with edits, which looks like Desktop/iCloud sync conflict copies. I'm not committing them. Pytest may collect the `test_* 2.py` copies inside the Desktop worktrees, which inflates counts. Moving the worktrees out of iCloud-synced folders would fix it.
