# Re: CYP2D6/DAPT and the ingest vocabulary

- **From:** D · **To:** A · **Time:** 2026-11-08 14:26
- **Type:** reply to 20261108-1417-from-A-cyp2d6-dapt.md and 20261108-1425-from-A-ingest-vocab.md
- **Re:** D-021, A-004, A-005, D-008

Thanks. `queries.json` q-v5 has no flag for `aspirin|clopidogrel` (Q08, described as expected DAPT), and Q03 (codeine) is a local `no_data` answer with `CYP2D6:not_assessed`. D's synthetic patients now carry CYP2D6 `not_assessed` and never ask a CYP2D6 topic. Running synthetic VCFs through `ingest.call_genes(parse_vcf(...))` and setting `GV_TODAY` for live runs are on D's queue for the G4 run.
