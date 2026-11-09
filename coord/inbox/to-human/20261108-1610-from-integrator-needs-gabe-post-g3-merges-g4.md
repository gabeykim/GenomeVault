# Needs Gabe: four post-G3 PRs to merge, then declare G4

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 16:10
- **Type:** escalation (merges + gate)
- **Re:** to-integrator/20261108-1606-from-A-pr9.md, to-integrator/20261108-1655-from-B-main-green-g4.md, P9 G4 (18:15) and G5 freeze (18:30), D-035, D-036

**Item 1: open PRs.** Each touches only its owner's paths, and none changes a contract or an invariant.

| PR | Agent | Head | Class | CI | State |
| --- | --- | --- | --- | --- | --- |
| #9 | A | `1b17750` | Refines F2/M3: `core/capture.py` logs a one-time setup hint when the vision model is skipped (never label text) | pass | ready, A asked for a merge |
| #10 | B | `d74c0b5` | tests only: Wi-Fi off mid-sync keeps the groups already sent, then resumes | pass | ready |
| #11 | C | `c0c385b` | Refines F2/S2 (D-029): phone progress, `GV_OCR=vlm` warm-up, `/api/capture` in a worker thread, additive `vision` field on `/api/status` | running | **draft opened by integrator** (no PR existed) |
| #12 | D | `3fcab5a` | Advances P8: the hand-measured 7/7 label-reading figure (~4 s) in slides, submission and Q&A, scoped to the demo set | running | **draft opened by integrator** (no PR existed) |

**Item 2: G4.** B reports that on main `87d6e0a`, `DEMO=1 make eval && python -m eval.gate` (D-035) gives **22 pass, 0 warn, 0 fail**, and `make test` gives 1158 passed. A got the same 22/0/0 on the octopus rehearsal. P9 G4 also needs "charts in slides". `docs/charts/*.svg` came in with #4. #12 adds the measured vision-model figure.

**Recommendation.**
1. Merge #9 and #10 now. Use a merge commit, and wait for green CI.
2. Merge #11 and #12 once C and D mark them ready and CI is green. If they aren't ready by about 18:00, merge them anyway: both are stage-facing (S2), and G5 at 18:30 allows bug fixes only.
3. After the last merge, run `make test` and `DEMO=1 make eval && python -m eval.gate` on main. If the result is 22/0/0, write the G4-passed DECISIONS entry, bump PLAN to v1.3.4, and fold in A's refinement line: "capture logs a one-time setup hint when the vision model is skipped: WARNING with `GV_OCR=vlm`, DEBUG with `auto`, never label content." Also fold in C's line from c0c385b: "`GV_OCR=vlm` on stage, warm-up read at startup, `/api/status.vision`."

I merged nothing and did not declare G4, because gate rulings and merges are yours.
