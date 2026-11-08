# data/ (owner: A)

Everything here is **synthetic** (PLAN I1). Alex is an invented patient (PLAN P5).

- `alex_profile.json`: Alex's profile in the `Profile` contract shape. Phenotype vocabulary: `poor_metabolizer`, `normal_metabolizer`, `decreased_function`, `normal_sensitivity`. Flag keys use these exact strings.
- `alex.vcf`: synthetic VCF (GRCh38) listing only the PGx defining positions for CYP2C19, SLCO1B1, CYP2D6, CYP2C9 and VKORC1. `INFO/ALLELE` names the allele an ALT call defines; positions not listed are reference. `core/ingest.py` (A queue 5) turns it into genotypes and phenotypes.
- `buckets/` is owned by B.
