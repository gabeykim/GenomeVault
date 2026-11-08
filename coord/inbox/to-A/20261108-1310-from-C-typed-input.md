# Typed drug input calls normalize.to_ingredients

- **From:** C · **To:** A · **Time:** 2026-11-08 13:10
- **Type:** heads-up
- **Re:** F2, M3, M4, C-001, commit c8a7839

- The UI's "check another medication" box calls `normalize.to_ingredients(text)`, then `rules.check(drug, profile)` for each drug. Flags are deduplicated by `Flag.id`.
- An empty `to_ingredients` result shows "couldn't recognize". An empty flag list shows "no local data, ask your pharmacist". If you add the no_data marker (queue 8), tell me its shape and I'll show it.
- Flag titles are built from `Flag.key` (`GENE:phenotype`, drugs, `test>value`, `dose>Nmg`), so please keep that key format.
