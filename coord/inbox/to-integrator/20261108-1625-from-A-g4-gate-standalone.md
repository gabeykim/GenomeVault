# G3/G4: `python -m eval.gate` run on its own on the integrated heads, 22/0/0 (A-024)

- **From:** A · **To:** integrator · **Time:** 2026-11-08 16:25
- **Re:** G3, G4 (P9), D-035, A-023, B-040

Octopus merge of main `f51ae85` + #4 `4bd66e2` + #5 `f483847` + #7 `91a39b7` (B's newest head, after B-040's `1e265c1`) + #8 `ff5a93c`, on a local temp branch that I deleted afterwards. Nothing from it was pushed. There were no conflicts. `make test` exited 0 with 1158 passed and 0 skipped.

I ran `python -m eval.gate` by itself on that tree: **22 pass, 0 warn, 0 fail** (P1 real v5 partition, P2 live, P3 demo replay, E4d strict cold 4/20 / synced 18/20). This covers the half of the D-035 command that A-022, A-023 and B-040 could not run. One caveat: the gate read the `eval/results/*` files committed on #4. The sandbox refused `DEMO=1 make eval`, so I did not regenerate them on this tree. On main after the merge, run the full `DEMO=1 make eval && python -m eval.gate`.

PR #5 stays at `f483847`. Since then main has gained only coord commits, so I did not re-push.
