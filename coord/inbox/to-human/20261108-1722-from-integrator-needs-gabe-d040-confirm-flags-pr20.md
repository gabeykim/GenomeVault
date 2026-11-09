# Needs Gabe: confirm D-040, make the 18:00 flag call, decide on PR #20

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 17:22
- **Type:** escalation (invariants I4/I5, demo beats, gate merge; AGENTS.md §8, §9, §12)
- **Re:** to-integrator/20261108-1712-from-D-d040-confirm.md, 20261108-1724-from-B-flag-on-off.md, 20261108-1730-from-A-fuzzy-hyphen-fact.md, 20261108-1721-from-B-tail-v2-pr20.md; D-040, D-041, D-042; main `1e0d176`

The loop can't rule on these three because each touches I4/I5, a demo beat or a merge.

## 1. D asks you to confirm D-040 (one line needed)
Dhiaa recorded D-040 as accepted at 16:58 (backup integrator, D-033). Your 16:57 pass had told D to hold. D-041 and D-042 build on D-040, and #14–#17 are merged. D has paused deck, pitch, Q&A and submission changes until you write "D-040 confirmed" or "D-040 deferred".
**Recommendation: "D-040 confirmed".** The flags ship OFF (see 2), so D should present the work as "built and tested, off for the demo": the new eval goes in `docs/results.md`, plus one Q&A line. No slide should show it as live.

## 2. 18:00 ON/OFF call for GV_FUZZY, GV_TAIL, GV_DEMO_LIVE_FALLBACK
- B: flags on and flags off give the same results (1282 passed, G4 gate 22/0/0). B's ON advice depends on a real key and a hand-checked tail pair, and the live fallback has never run with a real key. With no key, keep OFF.
- A: in `app._swap`, a typo inside a hyphenated combo (`lisinoprl-hydrochlorothiazide`) shows "assuming lisinopril" but runs the check on hydrochlorothiazide only, so **X4 is missed silently**. That is a wrong answer, not `no_data`, so it is an I4 risk. C has a one-line fix requested; it isn't on main yet.
**Recommendation: all three OFF**, matching the 1717 note to Dhiaa. Scripted beats S1–S6 are the same either way, and the freeze is next. The only case for turning GV_FUZZY ON: C's `_swap` fix merges and Dhiaa re-runs the beats before the freeze.

## 3. PR #20 (B, tail-v2), CI green, `e47dbdd`
Groups the tail partition into frequency tiers. The statistical attacker drops from 0.59 to 0.15 on the tail (I5, D-040 part 2), and GV_TAIL still defaults OFF. It adds a 14.6k-line JSON plus small edits to `core/router.py` and `core/decoys.py`.
**Recommendation:** if GV_TAIL stays OFF (rec 2), the demo never runs this code. Hold it until after the beats and freeze unless there's time for a mini-gate (`make test` + `DEMO=1 make eval && python -m eval.gate`) and a re-pull on the demo machine. If you turn GV_TAIL ON, merge #20 first (merge commit), then re-run the beats.

Also open, CI green, no new information: #18 (A, tests only, hyphen case as non-strict xfail) and #19 (integrator, GV_INTENT, default off). Both are your merge call.
