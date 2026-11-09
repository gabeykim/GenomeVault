# A is ready for part 1 of the adaptive-questions proposal, if you accept it

- **From:** A · **To:** integrator (Gabe) · **Time:** 2026-11-08 16:57
- **Type:** info / readiness
- **Re:** proposals/20261108-1655-human-adaptive-questions.md (part 1), I4, F-normalize, G4/G5

A has not written any code for this. The proposal touches I4/I5 and has no ruling yet, so A keeps holding per your 1638 message and AGENTS §5.

If you accept part 1, A can land it behind `GV_FUZZY=1` in about 30 minutes, well before 18:00:

- `core/normalize.py` gets `suggest(text) -> list[dict]`, one dict per unmatched word: `{"token": str, "span": [start, end], "mode": "assumed" | "ask", "choices": [canonical names, 1 to 3]}`. Stdlib only (difflib plus a small Levenshtein), checked against the lexicon in `data/rules/drug_names.json`.
- It returns `assumed` only when exactly one candidate is within edit distance ≤ 2 and the next best is at least 2 further away. Every other case returns `ask`.
- A new authored list, `data/rules/lookalikes.json`, covers clonidine/clopidogrel/clozapine, hydroxyzine/hydralazine and a few more ISMP-style pairs. Any word close to a name on that list always gets `ask`.
- `to_ingredients()` stays exactly as it is, so I4 holds: a corrected name only reaches a key after C shows it to the user and the user's re-typed or confirmed text goes back through the normal exact path. With the flag off nothing changes.
- New tests in `tests/A/` cover a 20-item typo set (shared with D for E1/typo eval), zero silent substitutions on look-alikes, and flag off = no behavior change.

**Contract note:** `suggest()` is a new additive function that C calls. If you want it in `CONTRACTS.md`/`core/interfaces.py`, please fix the return shape there. Otherwise A will ship the shape above and C can code against it.

If you reject it or don't rule by 17:10, A does nothing and keeps holding for G5.
