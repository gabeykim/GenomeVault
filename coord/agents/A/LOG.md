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

### A-004 · 2026-11-08 14:17 · commit `3ce9f6d` · PLAN v1.2

- **Change:** Applied the D-021 PGx corrections. `data/alex_profile.json`: CYP2D6 genotype and phenotype are now `not_assessed`. `data/alex.vcf`: rs4986893 (CYP2C19 \*3) moved to GRCh38 chr10:94780653, CYP2D6 rows removed, header says genotypes are matched by rsID. `data/README.md`: position table; the five positions D-021 did not list are marked `position unverified; matched by rsID`. New `data/rules/expected_combinations.json` with `aspirin|clopidogrel` (EX-001, DAPT after a stent, shown only when the profile has `CAD_post_stent`). `core/rules.py`: the engine never reads CYP2D6 or any `not_assessed` phenotype, never emits an expected-combination key as a Flag, and has new helpers `expected_keys()`, `expected_notes(drug, profile)` and `expected_notes_all(profile)`. New `tests/A/test_pgx_corrections.py` (15 tests). PR #1 updated.
- **Why:** PLAN v1.2 P5 / D-021 and the integrator's 14:04 message.
- **Class:** Advances
- **Plan:** advances P5 (v1.2), F3, M4, D-021; refines M4 (shape of the informational note)
- **Refinements:** (1) A note is a plain dict `{id, key, text, source}`, not a Flag. `rules.expected_notes(drug, profile)` returns the notes for one drug against the med list, and `expected_notes_all(profile)` returns them for the whole list (one per key). (2) A note needs one of its `conditions` in the profile (`CAD_post_stent` for EX-001), so aspirin plus clopidogrel without a stent shows no note and no flag. (3) Unassessed genes are `NOT_ASSESSED = {"CYP2D6"}` plus any gene whose phenotype is `not_assessed`. Rules treat them as missing, and the `context_gene` evidence line is left out. (4) The CYP2D6 rows were removed from the VCF rather than kept with a placeholder, so ingest (queue 5) cannot call CYP2D6 by accident. (5) Genotype matching by rsID is in the test helpers now. The real matcher is `ingest.py` (queue 5).
- **Contract impact:** none (`rules.check` signature unchanged; the new helpers are in my module only, outside CONTRACTS)
- **Affects:** I: `mocks/alex_profile.json` (yours) still has CYP2D6 `*1/*1` / `normal_metabolizer`, so mock and real data differ on that one gene. Please set both to `not_assessed` (message sent). C: `tests/C/test_actions.py:56` expects "CYP2D6 \*1/\*1: normal metabolizer", which will fail once the app reads the real profile or the mock is updated. If you want the DAPT note in the UI, call `rules.expected_notes` (message sent). D: Alex has no CYP2D6 call. The `aspirin|clopidogrel` note is informational and not a flag (message sent). B: `all_keys()` is unchanged (no new rule keys). Lab bands answered (message sent).
- **Demo impact:** S3: same X1–X4. The UI can show a DAPT info line for aspirin + clopidogrel. The genes panel shows CYP2D6 as not assessed.
- **Tests:** `make test` → 82 passed (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok
- **Next:** queue 5, `ingest.py` (VCF → star alleles by rsID → phenotypes; CYP2D6 → not_assessed) + `graph.py` (`load_profile`, labs older than 90 days stale), then 6 (`capture.from_image`, D-020)

### A-005 · 2026-11-08 14:24 · commit `bc29bd4` · PLAN v1.2

- **Change:** New `core/ingest.py` (M1) reads a VCF and matches it by rsID (never by position, and the VCF's INFO tags are ignored) against the new `data/pgx_alleles.json`. It produces genotypes and CPIC phenotypes for the 5 P5 genes: CYP2C19 (\*2, \*3, \*17), CYP2C9 (\*2, \*3), SLCO1B1 (\*1B, \*5, \*15 = \*1B + \*5), VKORC1 (-1639G>A), and CYP2D6, which is always `not_assessed` (D-021). `ingest.ingest()` combines the VCF genotypes with the records (meds, conditions, allergies, labs) from `data/alex_profile.json`. New `core/graph.py` (M2) stores the profile in SQLite. `graph.load_profile() -> Profile` (CONTRACTS) marks a lab `stale` when it is more than 90 days older than today. The graph lives in memory, or in a file if `GV_GRAPH_DB` names one (ingested on first use, then re-read). `GV_TODAY=YYYY-MM-DD` pins "today". New `tests/A/test_ingest_graph.py` (33 tests). `data/README.md` updated. PR #1 updated.
- **Why:** BRIEF queue 5. `graph.load_profile` is a G1 contract, and C's `app.py` already resolves `graph.load_profile` before falling back to the mock.
- **Class:** Advances
- **Plan:** advances F1, M1, M2, P5, D-021; refines M1/M2 (details below)
- **Refinements:** (1) Stale means `lab.date < today - 90 days`. Exactly 90 days is not stale. (2) `GV_TODAY` pins the date and `GV_GRAPH_DB` picks file storage. The default is in-memory, rebuilt on each call, so no generated files land in the repo. (3) A missing call (`./.`), a REF/ALT mismatch, a multi-allelic ALT, more than 2 variant alleles or an untabled diplotype gives genotype and phenotype `indeterminate`. No rule key uses it, so it never flags (I4). (4) An rsID absent from the VCF is reference, per the synthetic file's header. (5) An unphased SLCO1B1 388/521 double het reads `*1/*15 or *1B/*5`, and both readings are `decreased_function`. (6) Ingest can produce phenotype names Alex doesn't have, all CPIC snake_case: `intermediate_metabolizer`, `rapid_metabolizer`, `ultrarapid_metabolizer`, `normal_function`, `poor_function`, `increased_sensitivity`, `high_sensitivity`. (7) The graph takes genotypes from the VCF. The ones in `alex_profile.json` are reference only, and a test keeps the two equal.
- **Contract impact:** none. `graph.load_profile()` matches CONTRACTS. The optional `db`/`on` args are local extras.
- **Affects:** C: with A merged, `app._resolve("graph", "load_profile")` now gets real code. The 2025-10-20 eGFR comes back `stale=True`, and the rules evidence already tags it "(older than 90 days)". Nothing is required, but the UI can grey out stale labs (message sent). I: G1 check: X1–X4 fire from `graph.load_profile()`, which comes from the real VCF and records. Also FYI on `GV_TODAY` for demo rehearsals after 2027-01-26, when the latest labs go stale (message sent). D: phenotype vocabulary and `indeterminate`. E-checks can use `GV_TODAY` (message sent). B: FYI only. The phenotype names match your v4 keys (`SLCO1B1:poor_function`, `VKORC1:high_sensitivity`, `CYP2C19:intermediate_metabolizer`/`ultrarapid_metabolizer`), and no new rule keys were added (message sent).
- **Demo impact:** S3: same X1–X4, now from the SQLite graph. The genes panel can show the called diplotypes. The old eGFR is marked stale.
- **Tests:** `make test` → 115 passed (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok
- **Next:** queue 6 `capture.from_image` (D-020: OCR on label image → normalize, `[]` if unreadable, typed fallback), then 7 and 8 (both may already be covered by X5 and the `no_data` path; I'll check and close them).

### A-006 · 2026-11-08 14:30 · commit `f9db84a` · PLAN v1.2

- **Change:** New `core/capture.py` with `from_image(data: bytes, mime: str) -> list[Drug]`, the CONTRACTS signature from D-020. It reads the label text and passes it to `normalize.to_ingredients`. It returns `[]` for anything unreadable and never raises. It also has `from_text(text)` (the typed fallback, same normalizer) and `demo_png(label_text)`, which builds a small synthetic PNG that carries label text. Text comes from two local sources: (1) embedded label text, meaning a PNG `tEXt`/`zTXt`/`iTXt` chunk with keyword `gv:label` or a JPEG comment segment starting `gv:label`; (2) the `tesseract` program, only if it is on PATH, run as a local subprocess with a 30 s timeout. New `tests/A/test_capture.py` (30 tests). PR #1 updated.
- **Why:** BRIEF queue 6, D-020 and the integrator's 14:04 message. This unblocks C's `POST /api/capture` (S2).
- **Class:** Advances
- **Plan:** advances F2, M3, S2, D-020; refines M3 (OCR sources)
- **Refinements:** (1) No new Python dependency and no network (I2). OCR is the optional system `tesseract` binary. Without it, only images with embedded label text are readable; a plain photo gives `[]`, and the UI falls back to typing. (2) `GV_OCR` = `auto` (default: embedded, then tesseract) | `embedded` | `tesseract` | `off`. (3) The image type comes from the magic bytes (png, jpeg, webp, tiff, bmp, gif). The stated MIME must start with `image/`, but a PNG sent as `image/jpeg` is still read. Uploads over 15 MB give `[]`. (4) The label text (name, Rx number, pharmacy) never leaves `capture.py` and is not logged. Only the `Drug` list is returned. (5) A label that names a drug twice ("CLOPIDOGREL 75 MG … Generic for PLAVIX") gives one `Drug` (normalize dedupes, first dose wins). A misspelled name gives `[]` (no fuzzy guess, I4).
- **Contract impact:** none (implements the D-020 signature exactly; extras are module-local)
- **Affects:** C: `app.py` can call `core.capture.from_image(bytes, content_type)` in place of the interfaces stub once PR #1 merges, and fall back to typed input on `[]`. `capture.demo_png("CLOPIDOGREL 75 MG TABLET")` makes a sample "photo" for the phone page and demo (message sent). I: real photos need `tesseract` installed on the demo laptop (`brew install tesseract`). It is optional, since demo-mode sample photos work without it; your call (message sent). D: none. E4 offline capture can use `demo_png`.
- **Demo impact:** S2: a sample label photo (embedded text) gives clopidogrel 75 mg with no network. A real camera photo works only if tesseract is installed. S6: `demo_png("IBUPROFEN 200 MG")` → ibuprofen → X5 offline.
- **Tests:** `make test` → 145 passed (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok
- **Next:** queue 8, the `no_data` marker for unlisted pairs (rules helper for the router). Queue 7 (X5) was done in A-003; I'll close it after one check.

### A-007 · 2026-11-08 14:39 · commit `7cf591f` · PLAN v1.2.1

- **Change:** Two additive helpers in `core/rules.py`. `key_state(key)` gives the PLAN P6 answer state of one exact key in the local curated tables: `known` if a rule, an expanded class rule or an expected combination covers it, otherwise `no_data`. `no_data_keys(drug, profile)` lists the drug-drug pair keys between `drug` and the profile's other meds that no table covers (sorted, one per key). `rules.check` is unchanged. New `tests/A/test_no_data.py` (7 tests). PR #5 is open (PR #1 was merged at G1).
- **Why:** BRIEF queue 8: an unlisted pair gives no flags plus a `no_data` marker. It also gives S6 a local check that `clopidogrel|pantoprazole` stays `no_data` while `clopidogrel|omeprazole` is known (I4, no extrapolation).
- **Class:** Refines
- **Plan:** advances I4, P6 answer states, S6; refines M4
- **Refinements:** (1) A key is `known` locally if it is in `rules.all_keys()` (gene_drug, drug_drug, drug_lab, class rules expanded over their listed members) or in `expected_combinations.json`. Anything else is `no_data`. (2) `none_listed` needs a curated "listed as no interaction" table with a source. None is authored, so `key_state` never returns it today. I won't invent such entries without a citable source. (3) Keys on genes in `NOT_ASSESSED` (CYP2D6) are always `no_data` (D-021). (4) The marker covers drug-drug pairs only, not gene or lab keys.
- **Contract impact:** none (additive, module-local; not in CONTRACTS)
- **Affects:** B: optional. `router.route` already returns `no_data` for keys outside the bucket universe, so nothing is required. `rules.key_state` / `no_data_keys` let the router or KB tell "no local entry" apart before going to buckets (message sent). C: optional. The UI can show "no entry for this exact pair; ask your pharmacist" for `no_data_keys` (I7 wording) → no message, see B note. D: none.
- **Demo impact:** S6 no-extrapolation: pantoprazole gives no flag, and `clopidogrel|pantoprazole` is marked `no_data` locally.
- **Tests:** `make test` → exit 0, 152 passed; `check_ownership.py --range origin/main..HEAD` → ownership ok
- **Queue:** 7 (X5) closed. It was done in A-003, and `tests/A/test_alex_flags.py::test_ibuprofen_gives_x5_on_four_exact_keys` covers it. 8 is done with this entry. The core queue (1–8) is complete.
- **Next:** stretch: encryption at rest for the SQLite graph (stdlib only, no new dependency), or a merged run with B/C/D branches against the real A code. I'll take requests from C/D first.

### A-008 · 2026-11-08 14:44 · commit `f634d24` · PLAN v1.2.1

- **Change:** `data/rules/drug_names.json` v2 now names every drug in B's bucket universe (`data/buckets/v5.json` on B's branch: 103 drugs, 78 of which `normalize` could not read), plus codeine and St. John's wort, with common US brands (Celexa, Lexapro, Bactrim DS, Tylenol with Codeine, Depakote...). `core/normalize.py` now tokenizes table names the same way as input text, so "St. John's Wort" and "st johns wort" both match. New `tests/A/test_universe_names.py` (21 tests, 1 skipped on main). PR #5 updated.
- **Why:** I compared A's code against D's 20 eval questions (`eval/queries.json`, D's branch). Typed "citalopram", "codeine", "St. John's wort" or "Celexa" gave `[]`, so the question never reached the router (F2). The same was true for 78 of the universe's 103 drugs.
- **Class:** Refines
- **Plan:** advances F2, M3; refines M3
- **Refinements:** (1) Multi-word ingredient ids use underscores: `st_johns_wort`, which matches D's keys. (2) Salt forms collapse to the universe id: isosorbide mononitrate and dinitrate → `isosorbide`; valproic acid, divalproex and Depakote → `valproate`; rifampicin → `rifampin`; salbutamol → `albuterol`. (3) This adds names only, no rules. Meloxicam and piroxicam are NSAIDs but not listed class members, so they give no X5-style flag (I4). A test checks that Alex gets no flags from any new name. (4) `test_every_bucket_universe_drug_is_readable` reads the newest `data/buckets/v*.json` and skips until B's partition is on main.
- **Contract impact:** none
- **Affects:** B: after PR #5 merges, every v5 drug typed or photographed reaches `router.route` as the exact ingredient id. Nothing required. If a new bucket version adds a drug, the test above fails until I add the name (message sent). C: the typed box and `capture.from_image` read these names with no code change (message sent). D: Q03/Q05/Q16 drugs now normalize. Also, `rules.key_state("aspirin|clopidogrel")` is `known` locally (EX-001 DAPT note), but Q08's `offline_state` is `no_data` (message sent).
- **Demo impact:** none in S1–S6. Off-script typed questions (codeine, citalopram, supplements) now reach the router instead of silently doing nothing.
- **Tests:** `make test` → 173 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok. By hand against B's v5: 103/103 universe drugs normalize to themselves.
- **Next:** wait for PR #5 review. Answer D on Q08. Stretch: encryption at rest needs a crypto dependency (stdlib has no cipher, and I won't hand-roll one), so I'd raise it with the integrator before starting.

### A-009 · 2026-11-08 15:00 · commit `d621bd8` · PLAN v1.2.1

- **Change:** `core/ingest.py` can now also read a PharmCAT phenotype report (`*.phenotype.json`) alongside our own VCF caller. The new functions are `read_pharmcat(report)` and `merge_pharmcat(...)`, plus an optional `ingest(..., pharmcat=None)` argument. It accepts PharmCAT 2.x `geneReports` keyed by source (CPIC first) or directly by gene. Default behavior is unchanged: `graph.load_profile()` still calls `ingest()` with no report. New `tests/A/test_pharmcat.py` (9 tests, synthetic reports only, I1). PR #5 updated, and the branch is rebased on origin/main 64b66cb (last cycle's rebase had not been pushed).
- **Why:** BRIEF A stretch ("PharmCAT path"). It lets a user who already ran PharmCAT locally bring its calls in. Our own caller stays the default and the cross-check.
- **Class:** Refines
- **Plan:** advances M1, F1 (stretch); keeps I2, I4, D-021
- **Refinements:** (1) A PharmCAT call is used only when there is exactly one diplotype with exactly one phenotype, and that phenotype is already in `data/pgx_alleles.json` for that gene. Several diplotypes, "Likely ...", "Indeterminate", a missing phenotype, or an unknown term all give `indeterminate`, which no rule key uses (I4). (2) If PharmCAT and our VCF caller both give a phenotype and they differ, the gene is `indeterminate`; we don't pick one. A test shows a conflicting CYP2C19 report drops X1 rather than silently clearing it. (3) CYP2D6 is never taken from PharmCAT and stays `not_assessed` (D-021). (4) A gene the report doesn't mention keeps the VCF call. If the VCF couldn't call the gene, a clean PharmCAT call fills it. (5) PharmCAT itself is not run or bundled (it's Java). We read its JSON with stdlib only: no new dependency, no network (I2).
- **Contract impact:** none. `Profile` and `graph.load_profile` are unchanged. `ingest.ingest` gained an optional keyword argument, and only A's code calls it.
- **Affects:** none, so no messages. B-017's G2 test on real rules is unaffected because the default ingest is unchanged.
- **Demo impact:** none (S1–S6 use the VCF path)
- **Tests:** `make test` → 182 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok.
- **Next:** wait for PR #5 review at G2. The Q08 question to D is still open. The other stretch item, encryption at rest, needs a crypto dependency, so I'd ask the integrator first. Otherwise: requests from B/C/D.

### A-010 · 2026-11-08 14:54 · commit `3b2e4b1` · PLAN v1.2.1

- **Change:** New `tests/A/test_genotype_sweep.py` (18 tests). It builds a VCF for every 0/1/2-copy combination of each assessed gene's rsIDs (27 for CYP2C19, 9 for CYP2C9 and SLCO1B1, 3 for VKORC1), runs it through `ingest`, then runs `rules.check` on each gene-drug rule's drug at 10 mg and 40 mg. No code change. PR #5 updated, rebased on origin/main 1fb5eee.
- **Why:** Queue 1–8 is done. The ingest tests checked hand-picked genotypes and the rules tests checked Alex. Nothing checked the two together across all genotypes, so a rule whose phenotype ingest can never emit would never fire and nobody would notice.
- **Class:** Advances
- **Plan:** advances F1, F3, M1, M4, I4
- **Refinements:** none
- **Contract impact:** none
- **Affects:** none, so no messages.
- **Demo impact:** none
- **Tests:** `make test` → 200 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok. The sweep found no defects. Every rule phenotype (gene-drug and the drug-drug CYP2C19 context) is reachable from a VCF. Ingest only emits table phenotypes or `indeterminate`. Each gene-drug flag fires exactly for its phenotype and dose band, and never for `indeterminate` (I4).
- **Next:** wait for PR #5 review at G2. I asked the human whether to request `cryptography` for the encryption-at-rest stretch (to-human 1454). Until they answer, I'm taking requests from B/C/D.
