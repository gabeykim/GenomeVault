# B's D-040 flag recommendation (GV_TAIL, GV_DEMO_LIVE_FALLBACK)

- **From:** B · **To:** integrator (Gabe) · **Time:** 2026-11-08 17:24
- **Type:** recommendation (the 18:00 ON/OFF call)
- **Re:** D-040, D-041, B-066, B-067, PR #15 (head 414aa1c)

**Evidence.** Throwaway merge main 8171eb1 + #15 (414aa1c) + #16 (13374a9) + #17 (6088d6b):
- flags off: `make test` 1282 passed; flags on (GV_TAIL, GV_DEMO_LIVE_FALLBACK, GV_FUZZY): 1282 passed.
- eval with DEMO=1 and all three flags on, no key: G4 gate 22 pass / 0 warn / 0 fail. Numbers are the same as flags off.
- Gaps: no eval question names a tail pair, and the live fallback has not run with a real key (unit tests use a stubbed cloud only).

**Recommendation.**
1. **Demo machine has `ANTHROPIC_API_KEY` set and online:** turn `GV_TAIL=1` and `GV_DEMO_LIVE_FALLBACK=1` ON. A judge's off-script pair then gets a live answer, still sent as a whole bucket of 8 (I5). Before going on stage, ask one tail pair by hand (for example "can I take amoxicillin with my warfarin?" with a cold cache) and check that the ledger shows a `tail-NNNN` bucket and a real answer.
2. **No key, or the check in 1 fails:** keep both OFF. With the tail on and no key, every off-script pair reads `no_data`. That is honest (I4) but no better than flag off, and it adds tail cover traffic.
3. `GV_FUZZY` belongs to A; it is green in the same runs.

Either way, scripted beats S1 to S6 are unchanged (the same eval numbers).
