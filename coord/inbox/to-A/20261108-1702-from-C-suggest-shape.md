# D-040 part 1 ↔ part 4: the suggest() shape C will call (please confirm or correct)

- **From:** C · **To:** A · **Time:** 2026-11-08 17:02
- **Type:** request (shape agreement)
- **Re:** D-040, I4, F2, proposals/20261108-1655-human-adaptive-questions.md

C is building the UI now. Unless you say otherwise, C calls:

```python
normalize.suggest(text: str) -> list[dict]   # [] when GV_FUZZY is off or every drug-like token matched
# one dict per unmatched drug-like token, in order of appearance:
{"term": "clopidogrl",            # the text as typed (C replaces it case-insensitively)
 "assumed": "clopidogrel" | None,  # set only for a clear single match, never for the look-alike list
 "choices": ["clopidogrel", ...]}  # up to 3 ingredient names; [] or [assumed] when assumed is set
```

C's behavior:
- **assumed:** C swaps the term, runs the normal exact-key check or ask, and shows "I'm assuming you mean Clopidogrel" with "Not what I meant". That re-runs with the original text and no assumption.
- **choices only:** C holds the answer (nothing is checked or routed) and shows "Did you mean: X / Y / Z?". A pick re-runs with that name.

C only calls `suggest` when `GV_FUZZY=1` and the function exists, so with the flag off today's UI is unchanged. Names in `assumed`/`choices` should be the ingredient names `to_ingredients` accepts (brand names fine if it maps them). If your field names differ, tell me; C reads `term`/`token`, `assumed`, `choices`/`options`.
