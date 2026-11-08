# G1 passed: run evals against the real rules.check (D-022)

- **From:** integrator (Gabe, backup) · **To:** D · **Time:** 2026-11-08 14:31
- **Type:** gate notice (G1)
- **Re:** D-022, D-021, G1, P9, P7, M4

**G1 is merged.** `agent/A-data-rules` is on `main` (merge commit 7af15bf). A's real rules engine is live:
- Point your evals at `core.rules.check` / `rules.check_all` instead of mock flags; X1–X4 fire on Alex's discharge meds and X5 fires for ibuprofen.
- Per D-021, do **not** score `aspirin|clopidogrel` as a missed flag — it is expected DAPT shown as an informational note. The NSAID + antiplatelet case (ibuprofen, X5) is still a real flag.

Rebase onto `main`, re-read PLAN (now v1.2.1), and re-run your rule-dependent evals on the real engine.
