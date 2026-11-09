# Gabe: D-043 proof gate PASSED on the demo machine. Merge #22 → #20 → #18 → #21 → #19 → #23 now

- **From:** I (Dhiaa) · **To:** integrator (Gabe) · **Time:** 2026-11-08 17:51
- **Type:** request (priority, blocks freeze)
- **Re:** D-043, PRs #18–#23

On Dhiaa's demo laptop, with the key set and online, on `integrator/rehearsal-1750` (eea2501 = main 62b0e39 + #22 b991470 + #20 f4891e2 + #18 e34e618 + #21 c6e05f4 + #19 ecbf7c6 + #23 5398fad), all five flags ON:
`scripts/demo_proof.py` → **30 passed, 0 failed, 0 skipped**, including the live long-tail answer (abacavir|amoxicillin, tail-0841, group of 8, 0 personal fields) and its on-device repeat (kb_hit).

Please merge those six PRs in that order with "Create a merge commit" (heads as listed; any later head needs a re-run). Dhiaa then pulls main, restarts the demo app, re-runs the beats, and we freeze.
