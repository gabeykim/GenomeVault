# data/ (owner: A)

Everything here is **synthetic** (PLAN I1). Alex is an invented patient (PLAN P5).

- `alex_profile.json`: Alex's profile in the `Profile` contract shape. Phenotype vocabulary: `poor_metabolizer`, `normal_metabolizer`, `decreased_function`, `normal_sensitivity`, `not_assessed`. Flag keys use these exact strings. CYP2D6 is `not_assessed` (genotype and phenotype): its gene deletions and duplications cannot be called from SNP data, so no rule may read it (PLAN P5, D-021).
- `alex.vcf`: synthetic VCF (GRCh38) listing only the PGx defining positions for CYP2C19, CYP2C9, SLCO1B1 and VKORC1. `INFO/ALLELE` names the allele an ALT call defines; positions not listed are reference. Genotypes are matched by **rsID** (the `ID` column), never by position. `core/ingest.py` (A queue 5) turns it into genotypes and phenotypes.
- `rules/`: curated rule tables read by `core/rules.py` (M4). `rules/expected_combinations.json` lists combinations that are expected therapy (e.g. `aspirin|clopidogrel`, dual antiplatelet therapy after a stent). They never produce a Flag; `rules.expected_notes()` returns them as informational notes (D-021).
- `buckets/` is owned by B.

## VCF positions (GRCh38)

| rsID | Gene / allele | Position | Status |
| --- | --- | --- | --- |
| rs12248560 | CYP2C19 \*17 | chr10:94761900 | per dbSNP (D-021) |
| rs4986893 | CYP2C19 \*3 | chr10:94780653 | per dbSNP (D-021) |
| rs4244285 | CYP2C19 \*2 | chr10:94781859 | per dbSNP (D-021) |
| rs1799853 | CYP2C9 \*2 | chr10:94942290 | position unverified; matched by rsID |
| rs1057910 | CYP2C9 \*3 | chr10:94981296 | position unverified; matched by rsID |
| rs2306283 | SLCO1B1 \*1B (388A>G) | chr12:21176804 | position unverified; matched by rsID |
| rs4149056 | SLCO1B1 \*5 (521T>C) | chr12:21178615 | position unverified; matched by rsID |
| rs9923231 | VKORC1 -1639G>A | chr16:31096368 | position unverified; matched by rsID |

chr10:94775489 is rs17884712 (CYP2C19 \*9), not \*3; it is not in the file.
