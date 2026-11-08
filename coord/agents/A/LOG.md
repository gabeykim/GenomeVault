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

### A-002 · 2026-11-08 13:52 · commit `79d51d4` · PLAN v1.1

- **Change:** Added `core/normalize.py` (`to_ingredients(text) -> list[Drug]`, exact contract signature), `data/rules/drug_names.json` (≈55 brand/synonym names → generic ingredients, including Alex's meds, ibuprofen/NSAIDs, pantoprazole and common combination pills), and `tests/A/test_normalize.py` (22 tests). PR #1 updated.
- **Why:** BRIEF A queue item 2. Real normalizer behind C's typed box (F2) and, later, OCR capture (queue 6).
- **Class:** Refines
- **Plan:** advances F2, M3; refines M3
- **Refinements:** (1) Names are matched exactly (case-insensitive, longest multi-word name first). There is no fuzzy matching, so a misspelling returns `[]` instead of a guessed drug (same spirit as I4). (2) Combination pills return one `Drug` per ingredient, in label order. Strengths like `10/12.5 mg` are split across ingredients; if the count doesn't match, `dose_mg` is `None`. (3) The dose is read from the text between a name and the next name: `75 mg`, `75mg`, `0.081 g`, or a bare number right after the name (`aspirin 81`). A bare count followed by a word (`2 tablets`) is not a dose. Doses are converted to mg. (4) Text naming several drugs returns all of them in order, one entry per ingredient (the first dose wins). (5) Every ingredient in the table is also recognized under its own name.
- **Contract impact:** none
- **Affects:** C: `app.py`'s typed box gets the real `normalize.to_ingredients` once PR #1 merges. Same signature, ingredients lowercase → none. B: `ibuprofen` and `pantoprazole` normalize to those exact ingredient strings → none. D: E2/E4 scripted questions can pass brand names → none.
- **Demo impact:** S2/S6: typing "Advil" or "Plavix 75 mg" now resolves to real ingredients (after G1 merge).
- **Tests:** `make test` → 30 passed (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok
- **Next:** queue item 3, rule tables (`gene_drug`, `drug_drug`, `drug_lab`, `class_rules`), then 4 (`rules.check`, G1 14:30)

### A-003 · 2026-11-08 13:59 · commit `6e484af` · PLAN v1.1

- **Change:** Added the rule tables `data/rules/gene_drug.json`, `drug_drug.json`, `drug_lab.json`, `class_rules.json` and `flag_ids.json` (exact keys, dose conditions, `curated` tier, source and neutral text per entry), and `core/rules.py` with `check(drug, profile) -> list[Flag]` (contract signature) plus a helper `check_all(profile)` (one flag per key across all meds) and `all_keys()`. New tests `tests/A/test_rule_tables.py` (schema, exact keys, pantoprazole absent) and `tests/A/test_alex_flags.py` (X1–X5). PR #1 updated and marked ready for G1.
- **Why:** BRIEF A queue items 3 and 4, the G1 deliverable: X1–X4 fire from real data.
- **Class:** Refines
- **Plan:** advances F3, M4, P5, G1; refines M4
- **Refinements:** (1) Flag ids: a key listed in `flag_ids.json` gets its PLAN P5 id (X1..X5); any other key gets the id of the rule that produced it (`GD-`, `DD-`, `DL-`, `CR-` + number). (2) X5 is four flags that share id `X5`, one per exact key: `aspirin|ibuprofen`, `clopidogrel|ibuprofen`, `ibuprofen|lisinopril` (engine `class_rule`) and `ibuprofen|egfr<60` (engine `drug_lab`), all high, `needs_cloud` false. (3) Drug–lab rules fire on the most recent result for that lab; a stale result still fires and the evidence says "(older than 90 days)". Drug–lab keys put the drug first (`ibuprofen|egfr<60`), not sorted. (4) Dose conditions use the checked dose, else the dose of the same ingredient on the med list; if neither exists the flag still fires with "dose not stated" in the evidence (I7: prepare, never reassure). A known dose at or below the threshold gives no flag. (5) Class rules (I4) cover only listed members: NSAID = ibuprofen, naproxen, celecoxib; antiplatelet = aspirin, clopidogrel, prasugrel, ticagrelor; ACE inhibitor = lisinopril. Aspirin is not in the NSAID class. An explicit drug–drug entry wins over a class expansion. (6) `check` returns one flag per key, so X2 shows up from both the clopidogrel and the omeprazole side; callers that check every med should dedupe by key (or use `check_all`). (7) Kept out on purpose so D's offline `no_data` expectations hold: `aspirin|clopidogrel`, `lisinopril|simvastatin`, `amlodipine|simvastatin`, codeine, citalopram, warfarin, simvastatin with CK/ALT, and `clopidogrel|pantoprazole` (S6).
- **Contract impact:** none. `rules.check` matches CONTRACTS.md. For Alex, `check_all` returns exactly `mocks/flags.json` (ids, keys, severities, engines, evidence, `needs_cloud`).
- **Affects:** C: `app.py` `_flags_for` dedupes by `flag.id`, which would collapse the four X5 flags into one → dedupe by `flag.key` (message sent). Flags from non-P5 rules carry ids like `CR-001`. B: keys unchanged from my 13:52 message; every table entry has curated `text` + `source`, which you could seed as `curated` KB facts (optional) → none required (message sent). D: Q01–Q20 local expectations hold; naproxen (Q17) gives three `class_rule` flags with ids `CR-001`/`CR-002`; Q02 without a dose still gives X3 from the med-list dose → none (message sent). I: PR #1 is ready for the G1 merge; `graph.load_profile` is still the mock until queue 5.
- **Demo impact:** S3: X1–X4 come from the real engine after the G1 merge. S6: ibuprofen X5 works offline from local rules; pantoprazole gives no flag.
- **Tests:** `make test` → 67 passed (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok
- **Next:** queue item 5, `ingest.py` (VCF → star alleles → phenotypes) + `graph.py` (`load_profile`, labs older than 90 days marked stale)
