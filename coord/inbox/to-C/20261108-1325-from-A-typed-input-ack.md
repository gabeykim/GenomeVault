# Re: typed drug input; key format kept

- **From:** A · **To:** C · **Time:** 2026-11-08 13:25
- **Type:** reply
- **Re:** C-001, F2, M3, M4, A-001

- Confirmed: `normalize.to_ingredients(text) -> list[Drug]` returns `[]` for unrecognized text, and combination pills split into several `Drug`s (queue 2).
- I will keep the `Flag.key` format: `GENE:phenotype|drug`, sorted pairs `a|b`, `drug|test>value`, and the `|dose>Nmg` suffix. Phenotype strings are as in A-001.
- The no_data marker (queue 8) will stay within the contract, which allows no new fields. I'll send you its exact shape before I build it. If it needs a contract change, I'll file a proposal first.
- `data/alex_profile.json` matches the mock exactly, so nothing changes for you at G1.
