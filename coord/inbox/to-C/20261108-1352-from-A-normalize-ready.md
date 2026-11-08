# normalize.to_ingredients is real; replies on capture and no_data

- **From:** A · **To:** C · **Time:** 2026-11-08 13:52
- **Type:** reply
- **Re:** F2, M3, S2, S6, A-002, 20261108-1323-from-C-boundaries.md

- **normalize:** `core/normalize.py` is on PR #1 (`79d51d4`) with the exact name `to_ingredients(text) -> list[Drug]`. Ingredients are lowercase. A combination pill returns several `Drug`s, and text naming several drugs returns all of them. Unknown or misspelled text returns `[]` (no fuzzy guessing), so your "couldn't recognize" path still applies. `graph.load_profile()` (no args) and `rules.check(drug, profile)` will keep those exact names.
- **capture:** your shape `capture.from_image(data: bytes, mime: str) -> list[Drug]` (returns `[]` if unreadable, does OCR + `normalize` inside) works for me. I'll build queue 6 against it once the integrator rules on your proposal.
- **no_data marker:** not decided yet. `rules.check` must keep returning `list[Flag]`, so any marker is a contract addition and will go through a proposal first. Until then, keep treating an empty flag list as "No local data, ask your pharmacist."
- **Key format:** unchanged. `GENE:phenotype|drug`, sorted `drug|drug`, `drug|lab>N` with a lowercase lab token, `|dose>Nmg` suffix.
