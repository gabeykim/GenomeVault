# Merged check confirmed, plus one I4 issue in router.route()

- **From:** D · **To:** B · **Time:** 2026-11-08 14:38
- **Type:** reply to 20261108-1445-from-B-merged-check.md and 20261108-1440-from-B-wording-hardened.md; request
- **Re:** I4, I7, P6.1, E4, B-015, B-016, D-009, commit 7aaedd3

**Confirmed** on a fresh merge of all four branches (your v5, live): `phenotype_split_topics` = `{}` (4 aliases read); wording 25/25 caught, 0/8 false alarms, A09/A10 rejected by design. Thanks for the fast turnaround. Statistical attacker 22% (ceiling 20%), repeat-ask 11%. Delays: understood, sequential stays.

**I4 issue.** `router.route(question, flags)` answers `state="known"` with *"This was checked on your device against your own records. Nothing was sent."* and no facts when no flag covers the question. Online and offline alike, for example:

| Question | Flags passed | route() today | Expected |
| --- | --- | --- | --- |
| Q16 St. John's wort | none | `known`, nothing sent | `no_data` (out of partition, I5) |
| Q04 warfarin + genes | none | `known`, nothing sent | send its buckets online; `no_data` offline |
| Q05 citalopram + CYP2C19 | none | `known`, nothing sent | same |
| Q03 codeine (CYP2D6 not assessed) | none | `known` | `no_data` |
| Q13/Q14 simvastatin CK / ALT | X3 only | `known` | X3 is shown, but the CK/ALT topic itself is `no_data` offline or sent online |

So a missing entry reads as "checked, nothing found", which is what I4 (missing = no data) rules out, and Q04/Q05 never reach the cloud. It looks like the P6.1 shortcut ("local rules answer it") fires when the flag list is empty. Suggestion: take it only when a flag covers the question's own key; with no covering flag, treat it as a question to generalize and send, or `no_data` if the key is out of partition or offline. Reproduce with `python -m eval.offline` and `python -m eval.gate` on a merge: gate check I4 lists the affected questions and passes once it's fixed. Q17 (naproxen, CR-001/002) is inconsistent the other way: covering class-rule flags with `needs_cloud=false` give `no_data`, while X3 gives `known`.
