# Agent A — data-rules

**Mission:** turn Alex's raw data and any new drug into correct, exact-key flags (F1–F3, M1–M4).
**Owns:** `data/` (not `data/buckets/`), `core/ingest.py`, `core/graph.py`, `core/capture.py`, `core/normalize.py`, `core/rules.py`, `tests/A/`
**Provides to others:** `graph.load_profile`, `normalize.to_ingredients`, `rules.check`, flags X1–X5 (PLAN P5).
**Depends on:** contracts only.

## Queue (in order, each ≤ 45 min)

1. `data/alex_profile.json` + `data/alex.vcf` matching P5. Done: loads into `Profile`.
2. `normalize.py` + `data/rules/drug_names.json`: brand → ingredient, combination pills split. Done: "Plavix" → clopidogrel; unknown → `[]`.
3. Rule tables (`gene_drug`, `drug_drug`, `drug_lab`, `class_rules`) with exact keys, dose conditions, trust tier, source. Done: schema test passes; `clopidogrel|pantoprazole` absent.
4. `rules.check()` → X1–X4 for discharge meds. Done: `tests/A/test_alex_flags.py` green. **Gate G1.**
5. `ingest.py` (VCF → star alleles → phenotypes for 5 genes) + `graph.py` (SQLite, labs older than 90 days marked stale).
6. `capture.py`: OCR on label image → `normalize`; typed fallback.
7. X5: ibuprofen via authored NSAID + antiplatelet class rule and drug–lab rule.
8. Unlisted pair returns no flags plus a `no_data` marker for the router.

**Stretch:** PharmCAT path; encryption at rest.
