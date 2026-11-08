# From B to D: brand-name questions are now I4-safe (B-019)

- The router matched only bare ingredient words. "Is Plavix OK with Protonix?" with a local clopidogrel flag gave `known` (local), and the pair was never asked. It now goes through `normalize.to_ingredients`: online it gives `known` with the `clopidogrel|pantoprazole` fact, and offline it gives `no_data`/OFFLINE_TEXT.
- Suggestion: add one brand-name query to the E4/I4 set (expected `no_data` offline-cold, `known` online). This is optional.

Plan: I4, E4. Contract: none.
