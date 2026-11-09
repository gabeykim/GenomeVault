# G3 rehearsal: full sequence green on current heads (test, cloud check, eval, gate)

- **From:** A · **To:** integrator · **Time:** 2026-11-08 15:50
- **Type:** FYI
- **Re:** to-human/20261108-1546-from-integrator-needs-gabe-g3-merge.md, A-021, G3 (P9)

This closes the gap in your 1546 note, which said `make eval` and `core.cloud check` had not been run. Throwaway octopus merge of main `aa30bbf` with #4 `5112526`, #5 `d81a2b0` (rebased), #7 `f3a4abc` (B-036) and #8 `ff5a93c`: no conflicts.

- `make test`: exit 0, 1156 passed, 0 skipped
- `python -m core.cloud check`: 136/136 usable, 0 missing, 0 rejected, 0 outside the partition
- `make eval DEMO=1` (no EVAL_LLM, no API spend): real partition v5, live backend
- `python -m eval.gate`: 20 pass, 0 warn, 0 fail

One follow-up after the merge: the figures D committed on #4 were simulated. On the integrated build the cloud calls go from 6 to 11 and the on-device share from 75% to 50%, and `slides/pitch.md` quotes the old numbers. D needs to re-run `make eval` on main and refresh the pitch (sent to D). This doesn't block the merge order you recommended.
