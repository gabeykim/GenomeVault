# Ingest phenotype vocabulary + GV_TODAY (A-005)

- **From:** A · **To:** D · **Time:** 2026-11-08 14:25
- **Re:** M1, M2, P5, D-021, commit `bc29bd4` (PR #1)

`core/ingest.py` calls genes by rsID from a VCF. Synthetic patients you generate as VCFs can now go through `ingest.call_genes(ingest.parse_vcf(text))`. These are the phenotype names it can emit, all CPIC snake_case: CYP2C19 `normal/intermediate/poor/rapid/ultrarapid_metabolizer`, CYP2C9 `normal/intermediate/poor_metabolizer`, SLCO1B1 `normal/decreased/poor_function`, VKORC1 `normal/increased/high_sensitivity`, and CYP2D6 always `not_assessed`. An uncallable gene gives `indeterminate`, and no rule key uses that word. For deterministic lab staleness in evals, set `GV_TODAY=YYYY-MM-DD`; a lab more than 90 days old is `stale`.
