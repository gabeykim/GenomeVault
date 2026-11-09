# Needs Gabe: merge calls on PRs #18–#22, and fix two PR #19 tests first

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 17:35
- **Type:** escalation (merges before G5, I4 risk; AGENTS.md §9, §12)
- **Re:** to-integrator/20261108-1723-from-A-pr19-suggest-ok.md, 20261108-1727-from-D-pr21.md, 20261108-1730-from-B-merge-rehearsal-flags.md, 20261108-1731-from-C-pr22.md, 20261108-1733-from-A-pr18-pr22-rehearsal.md; D-040, D-041, I4, G5; main `1c51c94`

The 1722 note (D-040 confirm, 18:00 flag call, PR #20) still stands. Here is what's new since then. All five PRs are open, mergeable, and CI green at the heads below.

## 1. PR #22 (C, `b991470`): closes the GV_FUZZY hyphen gap (I4)
C's `_swap` now swaps by span. Under `GV_FUZZY=1`, `lisinoprl-hydrochlorothiazide 10-12.5 mg` checks both drugs, so X4 shows up. A rehearsed #18 + #22 together: `make test` exits 0 with 1301 passed, no xfail and no skip, in either merge order. #22 also renders the optional intent fields (`understood_as`, `clarify`). When those fields are absent, as they are with GV_INTENT off, nothing on screen changes.
**Recommendation: merge #22, then #18.** It fixes a silent wrong answer (I4). If GV_FUZZY stays OFF, the fix is harmless. If you want GV_FUZZY ON at 18:00, it is the one condition the 1722 note set, and Dhiaa has to re-run S1–S6 afterwards.

## 2. PR #18 (A, `e34e618`): tests only
On its own the hyphen case is a non-strict xfail. Once #22 is in, that test passes. **Recommendation: merge after #22.**

## 3. PR #19 (integrator, `ed0d473`): two tests leak flags. Fix them before merging
B's throwaway merge of main + #18 + #19 + #20 had no conflicts and passed 1311 with flags off. With the flags exported, three tests fail. None of the failures is a router bug.
- `tests/I/test_intent.py::test_flag_off_by_default` fails when `GV_INTENT=1` is exported. Fix: `monkeypatch.delenv("GV_INTENT", raising=False)`.
- `tests/I/test_intent.py::test_drug_typos_are_never_repaired_here` fails under `GV_FUZZY=1`, because intent.py repairs `simvastain` through `suggest()` on purpose. Fix: pin GV_FUZZY off in that test, and optionally add a flag-on test that expects the repair.
- The third failure is C's `tests/C/test_adaptive.py::test_ask_routes_the_corrected_question` under GV_INTENT. B has already told C.

A read #19 against the real `normalize.suggest`/`to_ingredients` and found no mismatch (A-036). The loop cannot push to `integrator/intent`. **Recommendation:** apply the two test fixes yourself. Merge #19 only if there is time for a re-run, since GV_INTENT defaults OFF and the demo never exercises it. Otherwise hold it until after the freeze.

## 4. PR #21 (D, `606ffca`): presentation script, plus the D-040 tail eval follow-up
D describes it as one file (`slides/presentation_script.md`). The PR now also touches `eval/adaptive.py`, `eval/run_all.py`, `eval/results/*.json`, `docs/results.md` and `tests/D/test_d_adaptive.py`, because of the D-019 change "tail E1 follows TAIL_VERSION". D ran `DEMO=1 make test`: 1291 passed. **Recommendation: merge before G5.** It is D-owned, contains no product code, and the script is needed for the pitch. Once merged, re-run `DEMO=1 make eval && python -m eval.gate` so `docs/results.md` matches main.

## 5. PR #20 (B): head moved to `f4891e2`
The head added one test commit after the 1722 note ("single_candidates is unreachable…"). CI is green. The 1722 recommendation is unchanged.

Suggested order if you merge everything: #22 → #18 → #21 → (#20 if GV_TAIL ON) → (#19 after the test fix). Use merge commits. After the merges, run `make test` on main and do one beat run on the demo machine.
