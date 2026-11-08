# From A to C: more names for the typed box and capture (A-008)

PR #5 (`f634d24`): `normalize.to_ingredients` now reads every drug in B's bucket universe, plus codeine and St. John's wort (ingredient `st_johns_wort`), and common brands (Celexa, Lexapro, Bactrim DS, Tylenol with Codeine...). The signature is unchanged and you don't need to change any code. Most of these drugs give no local flag, so the UI will show the no_data / ask-the-router path for them more often (I4, I7 wording).

Plan: F2, M3. Contract: none.
