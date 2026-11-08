# C status on your 15:20 list (G2 16:00, G3 17:30)

- **From:** C · **To:** human (Dhiaa) · **Time:** 2026-11-08 15:26
- **Type:** reply to 20261108-1520-from-human-whats-left.md
- **Re:** G2, G3, S1–S7, D-014, D-027, D-029, C-020…C-022, commit 80bf651

1. **G2 integration:** blocked on the merges. PRs #6, #2, #3 (and #5, #4) are open. On a local merge of main + all five: `make test` exit 0, **961 passed**, no mocks left in the app, network and ownership checks ok, and one question runs end to end with the live ledger (Q18 sends 2 groups, then a repeat gets a 0-B `kb_hit`). As soon as #6, #2 and #3 are on main I'll sync, drop the D-014 stand-ins, re-run it on main and report.
2. **Labels:** done (C-022). Seven flat, printed synthetic labels (the five discharge meds plus amoxicillin and ibuprofen) are in `phone/samples/`, with texts in `labels.json` shared with A. There's also a printable sheet at `/phone-assets/labels.html`.
3. **Demo path:** works on the local merge. Cold Q18 sends groups (S4); the repeat is a KB hit (S6); pantoprazole gets its own exact answer and "No local entry for pantoprazole with clopidogrel, …"; Sync stores 122 facts; with forced offline, ibuprofen gives 4×X5 and Q07, Q15 and Q19 are answered with 0 B; actions reach the phone. "Demo, not medical advice" shows in the header of every view. A test fails on any "safe" in `ui/` or `phone/`, and merge drops such sentences.
4. **Offline load:** OK. `ui/` and `phone/` load no CDN scripts, web fonts or remote images (tests enforce it), and the app needs nothing external to start.
5. **Rehearsal:** I'll run 2× demo mode and 1× live on the merged main by 17:30 and send D the timings.
