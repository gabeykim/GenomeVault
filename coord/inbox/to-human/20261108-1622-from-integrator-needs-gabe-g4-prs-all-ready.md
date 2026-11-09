# Needs Gabe: all four post-G3 PRs are ready and green. Merge them, then declare G4

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 16:22
- **Type:** escalation update (merges + gate)
- **Supersedes item 1 of:** to-human/20261108-1610-from-integrator-needs-gabe-post-g3-merges-g4.md (the recommendation there still stands)
- **Re:** to-integrator/20261108-1610-from-B-pr10-with-pr9.md, 20261108-1612-from-C-pr11-ready.md, 20261108-1617-from-D-pr12.md, 20261108-1619-from-C-pr11-hero.md, 20261108-1620-from-B-all-open-prs-merge-clean.md; P9 G4 (18:15), G5 freeze (18:30), D-035, D-037

**What changed since 16:10:** C and D marked #11 and #12 ready. CI passes on all four heads. B test-merged main `8946465` with all four PRs: no conflicts, `make test` exit 0, 1171 passed.

| PR | Agent | Head | Draft? | CI | Paths touched |
| --- | --- | --- | --- | --- | --- |
| #9 | A | `cf3df82` | no | pass | `core/capture.py`, `tests/A/` |
| #10 | B | `6dc7f25` (rebased again after B's test-merge, tests only) | no | pass | `tests/B/` |
| #11 | C | `4fe7735` | no | pass | `app.py`, `ui/`, `phone/`, `tests/C/` |
| #12 | D | `ec1d49b` | no | pass | `docs/`, `slides/`, `eval/run_all.py`, `tests/D/` |

New since the last note:
- **#11** has a 4th commit, `4fe7735` (C-027, F7). The page opens on a large centered GENOME / VAULT title that docks into the masthead on scroll. It is presentation only, with no API or contract change, and reduced motion skips it. C offers to split it out if you want only the vision-model part.
- **#12** has a 2nd commit, `ec1d49b`: the demo and video scripts from C's G3 rehearsal, plus a `docs/SETUP.md` line for `LOCAL_VLM_MODEL=qwen2.5vl:7b` in `.env`. The diff has no secrets (I checked for keys; only the variable *names* appear). D reports `DEMO=1 make test` 1158 and `python -m eval.gate` 22/0/0 on that build.

**Recommendation:** merge all four now with merge commits, in any order. B confirmed they merge clean. Keep `4fe7735` in #11, because it is UI-only and lands well before the G5 freeze. Then, on main, run `make test` and `DEMO=1 make eval && python -m eval.gate` (D-035). B's combined build did not run that second command. If the result is 22/0/0, write the G4-passed DECISIONS entry, bump PLAN to v1.3.4, and fold in the two refinement lines listed in the 16:10 note.

None of these PRs touches a contract or an invariant (I1–I8). I merged nothing and did not declare G4, because merges and gate rulings are yours.
