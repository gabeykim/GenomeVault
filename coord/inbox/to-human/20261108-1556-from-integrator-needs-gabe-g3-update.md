# Needs Gabe: G3 merge update. Full sequence now green; PR heads have moved

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 15:56
- **Type:** escalation update (gate merge)
- **Re:** to-human/20261108-1546-from-integrator-needs-gabe-g3-merge.md, to-integrator/20261108-1550-from-A-g3-full-sequence.md, G3 (P9, 17:30)

**Item.** A has now run the parts that were missing from the 15:46 note. A did a throwaway octopus merge of main `aa30bbf` with #4 `5112526`, #5 `d81a2b0`, #7 `f3a4abc` and #8 `ff5a93c`. There were no conflicts. Results:
- `make test`: 1156 passed
- `python -m core.cloud check`: 136/136 usable
- `make eval DEMO=1`, then `python -m eval.gate`: 20 pass, 0 warn, 0 fail

D reports 21 pass on its own branch with `DEMO=1`.

**Caveat.** Since that rehearsal, three PR heads have moved: #5 is now `1349212`, #7 is `079fe75` and #4 is `4bd66e2`. #8 is still `ff5a93c`. CI (`coord-ci`) is green on all four current heads.

**Recommendation.** Keep the merge order from the 15:46 note: #5, then #7, then #8, then #4. After the last merge, run `make test`, `python -m core.cloud check` and `DEMO=1 make eval && python -m eval.gate` on main (G4 command, D-035). On the integrated build the pitch numbers change: cloud calls go from 6 to 11 and the on-device share drops from 75% to 50%. D has been asked to refresh `slides/pitch.md`.
