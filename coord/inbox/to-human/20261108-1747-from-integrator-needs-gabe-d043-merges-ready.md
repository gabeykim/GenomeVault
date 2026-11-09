# Needs Gabe: D-043 merges are ready. Merge #22 → #20 → #18 → #21 → #19 → #23

- **From:** integrator (loop) · **To:** Gabe (cc Dhiaa) · **Time:** 2026-11-08 17:47
- **Type:** escalation (gate merges before G5; AGENTS.md §12)
- **Re:** to-integrator/20261108-1745-from-I-adaptive-on-merge-order.md, 20261108-1738-from-B-six-pr-rehearsal.md, 20261108-1739-from-A-d043-order-green.md, 20261108-1744-from-C-d043-checked.md; to-human/20261108-1744-from-D-stage-script-d043.md; D-043, D-040, I4, G5; main `fd6b627`

The loop does not merge. Here is the state for your merge call.

## The six PRs: open, CI green, current heads
| PR | Branch | Head | Note |
| --- | --- | --- | --- |
| #22 | agent/C-app-ui | `b991470` | fixes the combo-pill typo (X4 under GV_FUZZY, I4). Must land first |
| #20 | agent/B-privacy-router | `f4891e2` | unchanged since the 1735 note |
| #18 | agent/A-data-rules | `e34e618` | tests only. A is holding it |
| #21 | agent/D-eval | `bfa1adc` | **moved** from `c6e05f4`, which A and B rehearsed. The new commits are a main merge plus slides only (`presentation_script.md`, `demo_script.md`, `video_script.md`), so there is no code risk |
| #19 | integrator/intent | `ecbf7c6` | the 17:50 push Dhiaa expected has **not** landed. This is the head A, B and C rehearsed |
| #23 | integrator/demo-proof | `5398fad` | |

## Rehearsals (three independent throwaway merges, no conflicts)
- **A:** D-043 order. `make test` exit 0, 1335 passed, with flags unset and with all five set.
- **B:** a slightly different order with the same six heads. 1335 passed with DEMO unset, with DEMO=1, and with DEMO=1 plus all five flags. The B-069 flag-leak failures are gone.
- **C:** D-043 order. 1335 passed both ways. `demo_proof.py` gave 28 pass, 0 fail, 1 skip; the skip is the live long-tail answer, because there is no key in the sandbox. Browser check with all five flags: no console errors.

## One known gap (only in #19's tests, not in the product)
`tests/I/test_direct.py:10` and `tests/I/test_intent.py:10` call `os.environ.setdefault("DEMO", "1")`. A shell that exports `DEMO=0` gets 3 failures (`test_examples_lead_first[]`, `[1]`, `test_direct_reads_the_rewritten_question`). **Recommendation:** merge `ecbf7c6` as it is, and don't export DEMO=0 on the demo machine. If you have time, move the setting to a per-test `monkeypatch.setenv("DEMO", "1")` afterwards. The loop cannot push to `integrator/intent`.

## Recommendation
Accept the D-043 order. Use "Create a merge commit" for each PR, and merge #21 at `bfa1adc`. After merging:
1. Run `make test` on main.
2. Dhiaa pulls on the demo machine and runs `scripts/demo_proof.py` with `ANTHROPIC_API_KEY` set. If the live long-tail check fails, turn GV_TAIL and GV_DEMO_LIVE_FALLBACK off, as D-043 says.
3. Dhiaa says D's new stage line out loud once: "Does pantoprazole interact with my lisinopril?" should give no_data. It replaces the pantoprazole/omeprazole line, which stopped being true.
4. Then create `coord/FREEZE`.

Housekeeping: `integrator/rehearsal-1750` is 21 commits ahead of main with no PR. It is a throwaway rehearsal merge, so it should not get a PR. Delete it after G5 if you like.
