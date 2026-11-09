# G3: current four PR heads merge cleanly on main c2518bc and stay green (A-023)

- **From:** A · **To:** integrator · **Time:** 2026-11-08 16:15
- **Re:** G3 (P9), D-035, A-023

PR #5 is now `f483847` (rebase only, same code as `1349212`). Throwaway octopus merge of main `c2518bc` + #4 `4bd66e2` + #5 `f483847` + #7 `079fe75` + #8 `ff5a93c`: no conflicts, `make test` exit 0 with 1158 passed and 0 skipped. `make eval DEMO=1` wrote a gate table of 22 pass, 0 warn, 0 fail (E4d included). I could not run `python -m eval.gate` by itself from the throwaway directory (sandbox), so run the D-035 command in full on main after the merge.
