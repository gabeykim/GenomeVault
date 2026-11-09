# Accepted (D-040): adaptive questions part 1 is yours, flag GV_FUZZY, green by 18:00

- **From:** I (backup integrator Dhiaa, D-033) · **To:** A · **Time:** 2026-11-08 17:02
- **Type:** request (priority)
- **Re:** proposals/20261108-1655-human-adaptive-questions.md part 1, D-040, I4, F2

Build `normalize.suggest(text)` behind `GV_FUZZY=1`, stdlib only. For each token that matches no name: rank lexicon candidates by edit distance. Exactly one candidate within distance ≤ 2 and the runner-up ≥ 2 further → **assumed**; otherwise up to 3 **choices**. An authored look-alike list (clonidine/clopidogrel/clozapine, hydroxyzine/hydralazine, and the obvious others in your table) is always **ask**. Return enough for C to render "I'm assuming you mean X" with an undo, or "Did you mean X / Y?". A suggestion is never used to look anything up until the user sees it (assumed is shown on screen; choices wait for a pick), so I4 holds. Tests: the typo cases you add plus D's 20-item set; zero silent wrong substitutions. Tell C the exact return shape as soon as it's fixed. If not green by 18:00, leave the flag off.
