# Needs Gabe (by 17:10): ruling on the adaptive-questions proposal (touches I4, I5)

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 16:58
- **Type:** ruling request (invariant change, so it needs you)
- **Re:** proposals/20261108-1655-human-adaptive-questions.md, to-integrator/20261108-1655-from-human-adaptive-questions-ruling.md, I4, I5, I8, P6, D-039

Dhiaa approved this as a human owner and asked for a ruling by 17:10. It changes the wording of I4 and I5 and adds a send path, so under AGENTS.md §8 and the loop rules I applied nothing and routed nothing. Every agent has been told to keep working against PLAN v1.3.4 until you rule.

**My recommendation is to split it.** Accept parts 1 and 5 (typo set only) in ask-only form. Defer parts 2, 3 and 4 to the roadmap.

| Part | Recommendation | Reason |
| --- | --- | --- |
| 1 · A `normalize.suggest`, `GV_FUZZY=1` | **Accept, but ask only**: always show "Did you mean X?" chips and never auto-assume | It uses the standard library only and the corrected name goes back through the exact-key path. The "assumed" branch would answer under a guessed key before the user confirms it, which bends I4 ("exact-key facts only"). Ask-only makes zero silent substitutions true by construction. |
| 5 · D 20-item typo set | **Accept** | It tests part 1 and adds no new privacy claim. |
| 2 · B `tail-v1` partition, `GV_TAIL=1` | **Defer** | It needs a second partition in the I5 wording, a large new committed bucket file, and new E1 numbers that the proposal itself expects to be weaker. There is about an hour before freeze, and a weak privacy figure on a slide is exactly what a skeptical judge picks at (P8). |
| 3 · B `GV_DEMO_LIVE_FALLBACK=1` | **Reject for this build** | It weakens a guarantee we already rely on, that DEMO=1 never reaches the cloud. I8 and D-039 depend on it: the public Codespaces runs DEMO=1 with no key. |
| 4 · C consent to send "single, not hidden" | **Reject** | It sends a query with no decoy bucket. That breaks the P6 hiding guarantee I5 exists for, and AGENTS.md §8 says never weaken an invariant. B's `no_data` fix (`ccf2c4f`, already on main) covers the off-list case honestly. |

If you accept the split, the loop's next pass can record it in DECISIONS, bump PLAN to v1.3.5 with ask-only wording for I4, and send part 1 to A, the chip UI for part 1 to C, and part 5 to D, each behind its flag and shipped off if it isn't green by 18:00. If you would rather accept the whole proposal, say so in `to-integrator/` and I'll route parts 1 to 5 as written.
