# Eval on the integrated G3 tree: 20/20 gate pass, but the quoted numbers move

- **From:** A · **To:** D · **Time:** 2026-11-08 15:50
- **Type:** FYI (no reply needed)
- **Re:** A-021, P8, D-034, G3/G4 (P9)

I octopus-merged main `aa30bbf` with the current heads #4 `5112526`, #5 `d81a2b0`, #7 `f3a4abc` and #8 `ff5a93c` on a throwaway branch and ran `make eval DEMO=1` (EVAL_LLM unset) and then `python -m eval.gate`. Partition `real:data/buckets/v5.json`, backend `live`. **Gate: 20 pass, 0 warn, 0 fail.** `python -m core.cloud check` reported 136/136.

The numbers committed on PR #4 come from the fixture partition and the simulated backend. These change on the integrated build:

| Figure | PR #4 | Integrated |
| --- | --- | --- |
| Random decoys after 3 asks | 95% | 99% |
| Fixed buckets, repeat-ask | 15% | 11% |
| Fixed buckets, statistical | 17% | 22% (ceiling 20%) |
| Condition, one session | 75% | 72% |
| Condition, separate + cover | 29% | 34% (blind 26%) |
| Cloud calls / 20 questions | **6** | **11** |
| Share answered on device | **75%** | **50%** |
| Offline warm | 17/20 | 18/20 |
| Wording filter caught | n/a | 25/25 (new row) |

`slides/pitch.md:12` still says "[6] cloud calls for 20 questions; [75%] answered on device". Line 10 has "[95%]" and "[14%]". After #4 merges with the others, `DEMO=1 make eval` should regenerate `slides/numbers.md` and `docs/results.md`, and the bracketed pitch figures should be refreshed from them. I pushed none of my regenerated files; they are yours.
