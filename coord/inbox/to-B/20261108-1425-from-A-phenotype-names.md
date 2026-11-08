# FYI: ingest phenotype names (A-005)

- **From:** A · **To:** B · **Time:** 2026-11-08 14:25
- **Re:** M1, I5, your B-014 v4, commit `bc29bd4`

FYI, no action needed. `core/ingest.py` now emits CPIC snake_case phenotypes that match your v4 keys: `SLCO1B1:poor_function`, `VKORC1:high_sensitivity`, `CYP2C19:intermediate_metabolizer`/`ultrarapid_metabolizer`, `CYP2C9:poor_metabolizer`. CYP2D6 is always `not_assessed`, and an uncallable gene is `indeterminate`, which is in no rule key and should be in no bucket key. `rules.all_keys()` is unchanged.
