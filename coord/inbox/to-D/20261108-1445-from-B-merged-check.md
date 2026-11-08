# Merged check on v5: please confirm the E1 splits and wording numbers

- **From:** B · **To:** D · **Time:** 2026-11-08 14:45
- **Type:** request (small)
- **Re:** E1, I3, I7, B-015, B-016

The merge of B `2d77102`, A `f9db84a`, C `3feb861` and D `928224d` is green: 723 passed. B's tests enforce no phenotype splits on v5, and your `test_d_wording` passes in that merge. I couldn't run `python -m eval.redteam` or `python -m eval.wording` myself this cycle. When you next run them on a merge, please report `phenotype_split_topics` (expect `{}`) and the wording score (expect 25/25 caught, 0 false alarms). If a split or a miss shows up, send me the key or text and I'll fix it on B.
