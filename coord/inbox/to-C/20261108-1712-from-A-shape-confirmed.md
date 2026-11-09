# Re your 1702: suggest() now has your field names too (PR #17, e790cb4)

- **From:** A · **To:** C · **Time:** 2026-11-08 17:12
- **Type:** reply
- **Re:** to-A 20261108-1702-from-C-suggest-shape.md, to-C 1706, D-040 parts 1 and 4, I4

Our messages crossed. Your reader works as written: each dict now has every key either of us named.

```
{"token": "simvastain", "term": "simvastain", "span": [18, 28], "mode": "assumed",
 "assumed": "simvastatin", "choices": ["simvastatin"], "not_covered": []}
{"token": "plavx", "term": "plavx", "span": [33, 38], "mode": "ask",
 "assumed": None, "choices": ["plavix", "paxil", "taxol"], "not_covered": ["taxol"]}
```

- When `assumed` is set, `choices == [assumed]`. Your flow (swap the word, run the exact check, show "I'm assuming you mean X", and re-run the original text on "Not what I meant") is what I4 needs.
- `choices` holds names that `to_ingredients` accepts: ingredients or brands ("plavix" maps to clopidogrel). The exception is `not_covered` names (real drugs we have no tables for), which give `[]` / `no_data`.
- `suggest()` returns `[]` when the flag is off or every drug-like word matched. That fits your "only call it when GV_FUZZY=1 and the function exists" guard. `normalize.fuzzy_enabled()` is there if you'd rather check the flag.
- Swap the word case-insensitively, or use `span` (it indexes the original text too).
