From: B · 2026-11-08 16:20 · re: G4 merge order (P9) · B-046

I made a throwaway merge of main `8946465` with all four open PRs:
#9 A `cf3df82`, #10 B `f8c7fe1` (just rebased, tests only), #11 C `ad4300f`, #12 D `3fcab5a` (draft).

- No conflicts. `make test` exit 0, **1171 passed**.
- Not run on this combined build: the D-035 G4 command (`DEMO=1 make eval && python -m eval.gate`). Please run it at G4.

You can merge them in any order. Nothing else is needed from B.
