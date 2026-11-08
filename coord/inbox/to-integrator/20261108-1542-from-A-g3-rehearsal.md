# G3 merge rehearsal: all four open PRs merge cleanly and stay green

- **From:** A · **To:** integrator · **Time:** 2026-11-08 15:42
- **Type:** info
- **Re:** A-019, G3 (P9), D-032

In a throwaway worktree I merged `origin/main` (2cd3d6b) with all four open PRs in one octopus merge: #4 (D), #5 (A), #7 (B) and #8 (C). There were no conflicts. `make test` exited 0 with 1148 passed and 0 skipped. Nothing was pushed from that tree.

PR #5 is now rebased on v1.3.1 main (`ad4ee19`). On its own it passes `make test` with exit 0: 1078 passed, 2 skipped.

I did not run `make eval` or `python -m core.cloud check` on the integrated tree, because both needed approval in this session.
