# Needs Gabe: G3 gate merge — all four PRs green, rehearsal clean

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 15:46
- **Type:** escalation (gate merge)
- **Re:** to-integrator/20261108-1542-from-A-g3-rehearsal.md, G3 (P9, 17:30), D-032

**Item.** A merged `origin/main` (2cd3d6b) with all four open PRs (#4 D, #5 A, #7 B, #8 C) in a throwaway octopus merge: no conflicts, `make test` exit 0, 1148 passed. CI (`coord-ci`) is green on all four PRs. A did not run `make eval` or `python -m core.cloud check` on the integrated tree.

**Recommendation.** At G3, merge with "Create a merge commit" in dependency order: #5 (A, data/normalize) → #7 (B, router/pack sync) → #8 (C, UI, drops mock fallbacks) → #4 (D, evals/docs). After each, run `make test`; after the last, run `python -m core.cloud check` (expect 136/136) and `make eval` on main, then write the G3 DECISIONS entry and bump PLAN to v1.4.

**Optional (from A, to-human/20261108-1523):** real OCR/vision on real label photos is untested; if you want it checked before G3, start Ollama with `qwen2.5vl:7b`, set `LOCAL_VLM_MODEL`, and tell A. No action needed otherwise.
