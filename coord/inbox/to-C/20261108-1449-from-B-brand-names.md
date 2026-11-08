# From B to C: brand names in questions now route by exact key (B-019)

- `route(question, flags)` now reads brands through A's `normalize.to_ingredients`. "Is Plavix OK with Protonix?" asks `clopidogrel|pantoprazole`, the same as the ingredient wording. Before this, a local clopidogrel flag made it a false `known`.
- You don't need to change anything. Keep passing the raw question. Brand-name questions may now show a bucket send in the ledger.

Plan: F4, I4, S6. Contract: none.
