# FYI: combination strengths "10-40 mg" now parsed in ingredient order

- **From:** A · **To:** D · **Time:** 2026-11-08 15:18
- **Type:** FYI, optional eval case
- **Re:** F2, M3, M4 (X3), I7, A-014, commit fa0584b (PR #5)

- Before: "ezetimibe-simvastatin 10-40 mg" read as simvastatin 10 mg, so X3 (SLCO1B1 + simvastatin >20 mg) did **not** fire for a profile without simvastatin already on file. That was a false negative.
- Now: ezetimibe 10, simvastatin 40, so X3 fires. A range ("simvastatin 20-40 mg") gives dose `None`, and X3 still fires with the evidence "dose not stated" (I7).
- Optional E-case: `rules.check` on `to_ingredients("ezetimibe-simvastatin 10-40 mg")`, with simvastatin removed from Alex's meds, should give X3. Alex's scripted meds and the existing questions are unchanged.
