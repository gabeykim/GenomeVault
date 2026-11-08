# Agent A — impact log (append only)

Entries use coord/templates/impact-report.md and are numbered A-001, A-002, ...

### A-001 · 2026-11-08 13:25 · commit `ac60940` · PLAN v1.1

- **Change:** Added `data/alex_profile.json` (Alex in the `Profile` shape, same values as `mocks/alex_profile.json`), `data/alex.vcf` (synthetic GRCh38 VCF with only the PGx defining positions for the 5 genes), `data/README.md`, and `tests/A/test_alex_data.py` (4 tests).
- **Why:** BRIEF A queue item 1. This is the real data that `graph.load_profile` and `ingest.py` will read.
- **Class:** Refines
- **Plan:** advances F1, M1, P5; refines P5
- **Refinements:** (1) Phenotype strings are exactly `poor_metabolizer`, `normal_metabolizer`, `decreased_function`, `normal_sensitivity` (same as the mock), and gene–drug flag keys will use them. (2) VCF calls: CYP2C19 rs4244285 (*2) 1/1; SLCO1B1 rs4149056 (*5) 0/1 with rs2306283 0/0, so it is *5 and not *15; CYP2C19 *3/*17, CYP2C9 *2/*3, CYP2D6 *4/*10 and VKORC1 rs9923231 all 0/0. `INFO/GENE` and `INFO/ALLELE` name the gene and allele. (3) Condition strings stay as in the mock (`CAD_post_stent`, `hyperlipidemia`, ...). (4) The 2025-10-20 eGFR lab is stored with `stale` false. `graph.py` will set `stale` at load time (queue 5).
- **Contract impact:** none
- **Affects:** C: profile content is identical to the mock, so the switch at G1 changes nothing → none. D: can use the VCF and profile for eval fixtures → none. I: PR still needs opening (see STATUS) → open PR `agent/A-data-rules` → `main`.
- **Demo impact:** none yet. Feeds S3 at G1.
- **Tests:** `make test` → 8 passed; `check_ownership.py` → ok
- **Next:** queue item 2, `normalize.py` + `data/rules/drug_names.json`
