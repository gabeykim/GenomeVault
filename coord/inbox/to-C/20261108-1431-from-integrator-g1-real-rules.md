# G1 passed: switch to the real rules.check (D-022)

- **From:** integrator (Gabe, backup) · **To:** C · **Time:** 2026-11-08 14:31
- **Type:** gate notice (G1)
- **Re:** D-022, G1, P9, M4, S3

**G1 is merged.** `agent/A-data-rules` is on `main` (merge commit 7af15bf). A's real rules engine is live:
- Use `core.rules.check(drug, profile)` and `core.rules.check_all(profile)` instead of the mock `interfaces.check` / `mocks/flags.json`.
- X1–X4 fire on Alex's discharge meds; X5 fires for ibuprofen; `aspirin|clopidogrel` is an **informational** expected-DAPT note (A's `data/rules/expected_combinations.json`), not a flag.
- A also shipped `capture.from_image` (D-020) — the `POST /api/capture` path can call it now.

Rebase onto `main`, re-read PLAN (now v1.2.1), and switch S3's flags from mocks to the real engine.
