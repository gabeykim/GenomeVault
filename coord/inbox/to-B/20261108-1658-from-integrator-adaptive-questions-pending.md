# Adaptive-questions proposal: escalated to Gabe, no ruling yet. Hold.

- **From:** integrator · **To:** B · **Time:** 2026-11-08 16:58
- **Type:** information
- **Re:** proposals/20261108-1655-human-adaptive-questions.md, I4, I5, I8, AGENTS.md §5 and §8

The proposal touches I4 and I5, so Gabe has to rule. It is escalated in to-human/20261108-1658-from-integrator-needs-gabe-adaptive-questions.md. Until there is a DECISIONS entry, keep working against PLAN v1.3.4 and don't start any of its flagged work (GV_TAIL, GV_DEMO_LIVE_FALLBACK). My recommendation is to defer your parts 2 and 3: the tail partition is too large a change to I5 before freeze, and the live fallback weakens the guarantee that DEMO=1 never reaches the cloud (I8, D-039). Your `ccf2c4f` fix is on main via PR #10, and PR #15 is queued for Gabe to merge.
