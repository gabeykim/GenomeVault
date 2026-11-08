# G2 passed: real router + UI on main — re-run evals on the integrated build (D-032)

- **From:** integrator (Gabe, acting per D-024) · **To:** D · **Time:** 2026-11-08 15:35
- **Type:** gate notice (G2)
- **Re:** D-032, G2, P9, P7

**G2 is merged.** B's real `router.route`/`ledger`/`cloud` (merge 9d04dcc) and C's UI (merge be95c0e) are on `main`. Point your evals (E1–E4) at the **integrated build** now — real rules → real router → ledger (every entry `personal_fields_sent=0`), demo cache replay for E2/E4. Rebase onto `main`, re-read PLAN (v1.3.1). **Next: G3 17:30, G4 18:15** (your evals + charts on the integrated build).
