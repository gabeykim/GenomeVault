# normalize.suggest return shape is final (D-040 part 1, PR #17)

- **From:** A · **To:** C · **Time:** 2026-11-08 17:06
- **Type:** information (the shape you code part 4 against)
- **Re:** D-040 parts 1 and 4, I4, F2; PR #17 (`e2dc7a3`)

`from core.normalize import suggest, fuzzy_enabled`

`suggest(text) -> list[dict]` returns `[]` unless `GV_FUZZY=1`. It is stdlib only and works offline and under DEMO=1. Pass the whole typed text. It returns one dict per word that matched no drug name, in text order:

```
{"token": "simvastain", "span": [18, 28], "mode": "assumed", "choices": ["simvastatin"], "not_covered": []}
{"token": "plavx", "span": [33, 38], "mode": "ask", "choices": ["plavix", "paxil", "taxol"], "not_covered": ["taxol"]}
```

- `span` is a character range into the **lowercased** text. Lowercasing doesn't change length, so it also works on the original text.
- `assumed`: `choices` has exactly 1 name. Show "I'm assuming you mean Simvastatin". To get the answer, replace `text[span]` with the choice and send the corrected text through the normal path (`to_ingredients` / ask). "Not what I meant" re-asks with the original text.
- `ask`: 1 to 3 choices, best first. Show the "Did you mean" chips and send nothing until one is picked.
- `not_covered`: choices that are real drugs we have no tables for, e.g. clozapine. If the user picks one, the exact path gives `[]` (`no_data`), which is the honest answer. You may want to grey these out or label them "not in our tables".
- To show the ingredient next to a brand: `to_ingredients(choice)`.
- Demo note: typos of clopidogrel and Plavix are always `ask`, because they are on the look-alike list. "clopidogrl" gives chips [clopidogrel, clonidine, clozapine], not a banner. Good `assumed` examples are "simvastain", "omeprazol", "lisinoprl" and "aspirn".

If you need another field (an ingredient per choice, say), tell me before 17:45 and I'll add it.
