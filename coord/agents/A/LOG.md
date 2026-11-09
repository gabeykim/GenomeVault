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

### A-011 · 2026-11-08 15:00 · commit `143fa41` · PLAN v1.2.1

- **Change:** New allergy engine in `core/rules.py` (`_allergy`, `allergy_key`, `allergy_rule_keys`), driven by a new authored table `data/rules/allergy.json`. It has two groups, penicillins (amoxicillin, ampicillin, penicillin_v, penicillin_g, dicloxacillin, nafcillin, oxacillin, piperacillin) and sulfonamide antibiotics (sulfamethoxazole, sulfadiazine), each with aliases (`pcn`, `sulfa`, `sulfa drugs`...). `drug_names.json` v3 adds the members' brands and generics (Augmentin, Unasyn, Pen VK, Veetids, Bicillin, Zosyn, Septra...) so they can be typed or photographed. PR #5 updated, rebased on origin/main 01f4f28.
- **Why:** F3 (Must) lists allergy as one of the four checks, and `Flag.engine` already allows `"allergy"`, but no engine produced one. Alex's penicillin allergy (P5) was never checked, so "Amoxil" came back with no flag.
- **Class:** Refines
- **Plan:** advances F3, M4; keeps I4, I6, I7, I3
- **Refinements:** (1) Allergy keys are `allergy:<group>|<ingredient>`, the same shape as gene-drug keys, e.g. `allergy:penicillin|amoxicillin`. (2) An allergy on the record matches a group by its id or a listed alias, case- and space-insensitive, with no fuzzy matching (`penicilin` gives nothing). It flags only the group's listed members. (3) An allergy written as a member's own name (`amoxicillin`) matches that ingredient only (`allergy:amoxicillin|amoxicillin`) and never the rest of the group. (4) Nothing is inferred across groups: no penicillin → cephalosporin, no sulfa antibiotic → furosemide, HCTZ or celecoxib, and trimethoprim in Bactrim is not flagged (I4). (5) Severity is high, the source is curated FDA labeling (I6), `needs_cloud` is false, and the text says "tell the pharmacist or prescriber", never that something is safe (I7).
- **Contract impact:** none. `engine: "allergy"` was already in `Flag`. `all_keys()` and `key_state()` now include the allergy keys (`known`).
- **Affects:** B: the real allergy key is `allergy:penicillin|amoxicillin`, not the `penicillin|amoxicillin` your tests use. `validator._key_drugs` drops the `allergy:` part, so the only drug token is `amoxicillin`, and `generalize` already sends nothing for this engine → optional fixture update. C: allergy flags can now reach `actions.py` (the `engine == "allergy"` branch) and the UI's "Allergy" label → none required, worth a look in the demo. D: optional eval question "Alex is prescribed Amoxil → local allergy flag, nothing sent".
- **Demo impact:** none to S1–S6. Alex's discharge list has no penicillin, so `check_all` still gives only X1–X5. It could become an extra beat (photograph an Amoxil label → local allergy flag, zero bytes out).
- **Tests:** `make test` → 237 passed, 1 skipped (exit 0). New `tests/A/test_allergy.py` (37 tests). The allergy rules are also covered by the existing table schema tests, since `allergy` is now in `rules.TABLES`. `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok.
- **Next:** wait for PR #5 review at G2. The Q08 question to D and the crypto-dependency question to the human (to-human 1454) are still open. Otherwise: requests from B/C/D.

### A-012 · 2026-11-08 15:06 · commit `271985d` · PLAN v1.2.1 (D-029 pending in PR #6)

- **Change:** `core/capture.py` gains a third, local source for label photos: the vision model from D-029. `from_image` now tries embedded label text, then the VLM, then tesseract (`GV_OCR=auto`). New modes: `GV_OCR=vlm`. New functions: `vlm_drugs(data)` and `drugs_from_fields(brand, ingredient, strength)`. The VLM is called through `local_llm.generate(prompt, images=[b64], format="json", model=local_llm.VLM_MODEL)` and asked for `{brand_name, ingredient, strength_mg}`. New `tests/A/test_capture_vlm.py` (30 tests, fake model, no Ollama needed). `test_capture.py`'s no-network test now allows `local_llm` only, and its fixture turns the VLM off. PR #5 updated.
- **Why:** The integrator's heads-up for PLAN v1.3 (PR #6, D-029) routes label photos to a local VLM behind A's `capture.from_image`. Without it, a real photo with no embedded text reads only if tesseract happens to be installed, so S2 only worked on the bundled demo PNGs.
- **Class:** Refines (inside M3/D-020, no interface change). It is written so it is a no-op until PR #6 merges and `LOCAL_VLM_MODEL` is set. On main's current `local_llm` there is no `VLM_MODEL`, so the model is never called.
- **Plan:** advances F2, M3, S2, D-029 (pending); keeps I2 (localhost only, via `local_llm`), I4, I8 (embedded demo PNGs still read first with no model)
- **Refinements:** (1) Source order in `auto`: embedded, then VLM, then tesseract. The first source that reads anything decides. A VLM that reads a name not in the table gives `[]` and tesseract does not run. (2) The VLM only reads: brand and ingredient are each normalized through the exact-key table. If both resolve and neither ingredient set contains the other (e.g. "Plavix" with "simvastatin"), the answer is `[]`. If one contains the other ("Zestoretic" with "lisinopril"), the larger set is kept. (3) `strength_mg` is used only if it is a positive number or a plain strength string ("75", "75 mg", "20/12.5", "0.5 g"). It is handed to `normalize`'s own dose parser, so combination strengths split the same way as typed text. Anything else gives no dose. (4) The VLM is skipped and the next source runs if it is not configured (`VLM_MODEL` missing, empty or `set-me`), not running, or answers with something other than a JSON object naming at least one field. (5) The photo goes only to the localhost model. The model's answer is not logged or stored.
- **Contract impact:** none. `capture.from_image(data, mime) -> list[Drug]` is unchanged and still never raises.
- **Affects:** C: once `LOCAL_VLM_MODEL=qwen2.5vl:7b` is set and Ollama is running, real label photos read through the same `from_image` call. An empty list still means "fall back to typed input". Nothing required (message sent). D: optional E-case "photo of an unknown brand → [] and typed fallback, 0 bytes out" (message sent). I: uses PR #6's `local_llm.generate(images=, format=, model=)`. If that signature changes before merge, please tell me. B: none.
- **Demo impact:** S2 can use a real photographed label instead of a bundled PNG once PR #6 merges and the VLM is set. The bundled PNGs still read first, so the scripted S2 is unchanged.
- **Tests:** `make test` → 267 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok. Not tested against a live Ollama in this cycle.
- **Inbox:** D 1500 (Q08: keep `key_state`, the EX-001 note counts as backing) → closes my open question, no change. B 1502 (allergy keys OK; keep the `allergy:` prefix) → noted, no change.
- **Next:** check the VLM against a live `qwen2.5vl:7b` once PR #6 is on main, and record a couple of synthetic label photos for S2. Otherwise: PR #5 review at G2, requests from B/C/D.

### A-013 · 2026-11-08 15:12 · commit `9e94292` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** New `capture.label_drugs(text)`. Label text from the embedded and tesseract sources now goes through it instead of straight into `normalize.to_ingredients`. The text is cut into lines and sentences, and only the first piece that names a drug counts. If that piece has no strength, the strength comes from a later piece naming exactly the same ingredients ("PLAVIX" … "clopidogrel 75 mg"), or from the next line when name and strength were split ("LISINOPRIL-HCTZ" / "20-12.5 MG"). New `tests/A/test_capture_label_warnings.py` (12 tests). PR #5 updated.
- **Why:** Real labels name drugs the user is not taking in their warnings ("Do not take aspirin or other NSAIDs such as ibuprofen (Advil)"; OTC Drug Facts: "ask a doctor if you take aspirin … or a blood thinner such as warfarin"). Before this, a Plavix label with that warning gave clopidogrel + aspirin + ibuprofen, so one photo fired X5 for a drug the user never took. Typed input was never affected; the VLM path returns fields, not text, so it wasn't either.
- **Class:** Refines (inside M3, no interface change)
- **Plan:** advances F2, M3, S2; keeps I4 (a photo never adds a drug that isn't the labelled product)
- **Refinements:** a label photo is one product: the first line/sentence that names a drug decides, and a combination pill stays whole because both names are on that line. Sentences split on `. ; ! ?` followed by a space, so "12.5" stays whole. `from_text` (typed) still keeps every name.
- **Contract impact:** none. `capture.from_image(data, mime) -> list[Drug]` unchanged, still never raises.
- **Affects:** C: none. Both phone samples still read as clopidogrel 75 and ibuprofen 200 (checked). A real label photo through tesseract no longer shows warning drugs as flags (message sent). D: optional eval case "label with a warning naming ibuprofen → no X5" (message sent). B, I: none.
- **Demo impact:** S2 safer with a real photographed label: no spurious X5 from the warning sticker. The scripted S2 with bundled PNGs is unchanged.
- **Tests:** `make test` → 279 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok.
- **Inbox:** nothing new since A-012. Read B-024 (cloud thinking fix): no effect on A.
- **Next:** live test of the VLM path against `qwen2.5vl:7b` once PR #6 is on main. This needs Ollama, which the headless loop can't reach, so it may need the human. Otherwise: PR #5 review at G2, requests from B/C/D.

### A-014 · 2026-11-08 15:18 · commit `fa0584b` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** `normalize.to_ingredients` now treats names joined only by `-` or `/` ("ezetimibe-simvastatin", "lisinopril / hctz") as one combination product. The strengths after the last name are split on `-` or `/` and go to the ingredients in order ("10-40 mg" means ezetimibe 10, simvastatin 40). If the count doesn't match the ingredients (a range like "simvastatin 20-40 mg", or one number for two drugs), the dose is `None`. `drug_names.json` v4 adds the label abbreviations `amox clav` / `amoxicillin clav`. New `tests/A/test_combo_strengths.py` (18 tests, including an Amoxil label photo giving AL-001 end to end).
- **Why:** Found while checking C's Amoxil question (1510). "ezetimibe-simvastatin 10-40 mg" was read as ezetimibe None and **simvastatin 10 mg**, so X3 (SLCO1B1 + simvastatin >20 mg) stayed silent: a false negative. The same bug gave "lisinopril-hydrochlorothiazide 20-12.5" hydrochlorothiazide 20 mg, and "amlodipine-atorvastatin 5-40" atorvastatin 5 mg. `rules` already treats an unknown dose as "worth asking" (I7) and falls back to the profile dose, so a `None` is safe and a wrong guess is not.
- **Class:** Refines (inside M3, no interface change)
- **Plan:** advances F2, M3, M4 (X3 dose condition); keeps I7 (never reassure on a guessed dose)
- **Refinements:** P5 dose parsing: a combination's strengths may be written `a/b` or `a-b` and go to the ingredients in label order. A range or a count that doesn't line up gives `dose_mg=None`, never the first number.
- **Contract impact:** none (`to_ingredients(text) -> list[Drug]` unchanged; ingredient sets unchanged, except that "amox-clav" now also yields clavulanate)
- **Affects:** C: none required. `/api/check` on typed combos now shows correct strengths. Answer to C's 1510 question: an Amoxil label reads as amoxicillin 500 → AL-001 only, and the penicillin warning line is dropped (message sent). B: none (the router uses only ingredient names from `to_ingredients`). D: optional eval case "ezetimibe-simvastatin 10-40 mg → X3" (message sent). I: none.
- **Demo impact:** none for the scripted beats (Alex's meds and both phone samples unchanged). A typed or photographed combination label off-script now gets the right strengths.
- **Tests:** `make test` → 297 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok.
- **Inbox:** C 1510 (allergy + no_data wired) handled. Read B-025 (route covers only on-topic flags), B-026 (asked pair leads facts) and C-020 (sync, confirm, allergy, no_data). None of them needs a change from A.
- **Next:** live VLM test against `qwen2.5vl:7b` once PR #6 is on main (may need the human, since Ollama can't be reached from the headless loop). Otherwise: PR #5 review at G2, requests from B/C/D.

### A-015 · 2026-11-08 15:23 · commit `24c5148` · PLAN v1.2.1 (v1.3 pending in PR #6)

- **Change:** New `tests/A/test_capture_g3_labels.py` (56 tests), the G3 check the human asked for (to-A 1516). Six full synthetic pharmacy labels (aspirin 81 EC, clopidogrel 75, omeprazole DR 20, simvastatin 40, lisinopril 10, amoxicillin 500), each with header, Rx#, "Generic for" line, directions and a warning that names other drugs. Each runs through every local path: PNG iTXt, JPEG comment, faked tesseract text, and a faked vision-model reply (brand + ingredient, brand only, ingredient only). Each photo must flag exactly like the typed name. One fix in `core/capture.py`: `label_drugs` now skips **warning pieces**, meaning a sentence where a cue ("do not", "avoid", "tell your", "if you", "ask a", "such as", "may cause"…) comes before any drug name.
- **Why:** The new test found a false drug. When a label's product line can't be read (OCR misread "PLAVLX"), the one-product rule from A-013 took the first piece that named a known drug, which was the warning. "Avoid omeprazole" became **omeprazole**, so C's confirm step offered a drug Alex doesn't take, with a false X2 behind it. "Do not take aspirin or ibuprofen" gave aspirin + ibuprofen (a false X5). Such labels now give `[]`, and C's typed fallback opens (I4).
- **G3 results (to-A 1516):** all 6 labels give exactly one right Drug on every path: aspirin 81 → no flag; clopidogrel 75 → X1, X2; omeprazole 20 → X2; simvastatin 40 → X3; lisinopril 10 → X4; amoxicillin 500 → AL-001 only. No warning-line drug got through on any path. Unknown names ("PLAVLX", "FOOZOLAMIDE", header only, VLM reads "Plavlx"/"Foozol"/"Amoxyl") → `[]`. Brand/salt variants checked by hand also resolve: Ecotrin, Bayer low dose, clopidogrel bisulfate, Prilosec, omeprazole magnesium, Zocor, Zestril, Prinivil, amoxicillin trihydrate, amoxicillin 250 mg/5 ml. **Not tested:** real OCR or a real vision model on real photos. Neither tesseract nor Ollama is installed on this machine, so the live `qwen2.5vl:7b` check still needs the human.
- **Class:** Refines (inside M3, no interface change)
- **Plan:** advances F2, M3, S2, S6 (Amoxil bonus), G3; refines M3; keeps I4
- **Refinements:** M3 one-product rule: label sentences that open with a warning cue before any drug name are never the product line. A label with no readable product line gives `[]`, never a drug from its warnings.
- **Contract impact:** none (`from_image(data, mime) -> list[Drug]` unchanged; `[]` was already the "unreadable" answer)
- **Affects:** C: no change required. A misread label now opens typed input instead of a wrong drug (message sent). Both phone samples (`clopidogrel.png`, `ibuprofen.png` text) are unchanged. D: this strengthens the optional "Plavlx" look-alike red-team case. A look-alike plus a warning naming a real drug is a good variant (FYI only, no message). B, I: none.
- **Demo impact:** none for scripted beats (S2 Plavix photo, S6 Amoxil bonus unchanged)
- **Tests:** `make test` → 353 passed, 1 skipped (exit 0); `check_ownership.py --range origin/main..HEAD` → ownership ok; `check_network.sh` → network ok.
- **Inbox:** human 1516 (skip encryption; test capture for G3) handled: stretch dropped, G3 test done. D 1518 (optional cases after G4) noted. Read B-027, C-021, D-011: no effect on A.
- **Next:** live VLM run on real label photos when the human can start Ollama (after PR #6 merges). Otherwise: PR #5 review at G2, requests from B/C/D.

### A-016 · 2026-11-08 15:29 · commit `25cd41d` · PLAN v1.3

- **Change:** New `tests/A/test_eval_queries.py` (47 tests), the G2 support the integrator asked for (to-A 1522, D-030). No A code changed. (1) All 20 of D's q-v7 questions resolve through A's code with no silent miss. Each of the 13 drugs is an exact `normalize` key, both by its own name and inside the question text. Q14 ("my statin") names only a class and gives no Drug, by design (I4). Every key a question lists is either curated and actually fires for Alex (a flag, or the EX-001 note), or `no_data` on purpose. Each `no_data` pair is marked by `no_data_keys`. The expected X1–X5 and the CR-001/CR-002 class rules (Q17) fire. A frozen copy of q-v7 runs today; the same checks run on `eval/queries.json` once D's branch is on main. (2) The A→B handoff: `rules.check_all` gives plain contract `Flag`s that survive a JSON round trip. `route(question, flags)` returns a valid `Answer` and does not change the flags. Against B's real router (offline, cold KB), nothing is sent. Q02, Q11 and Q15 come back `known` from A's local-only flags (X3, X4, X5). X1 and X2 generalize into buckets in the partition. The router-only tests skip on main until G2.
- **Why:** This pins the G2 end-to-end path (rules → router) before the merge, so a drug name, key spelling or `needs_cloud` mark that drifts fails in A's tests first.
- **Verified against B's real router:** I overlaid A's code on `origin/agent/B-privacy-router` (`f2ca312`) in a scratch worktree, which has since been removed: 46 passed, 1 skipped. **Finding for B and D (not A code):** with the real router offline on a cold KB, 10 of D's `offline_state: known` questions come back `no_data`. These are Q01, Q06, Q18 and Q19 (the X1/X2 flags need the cloud and have no KB fact yet), Q12 and Q20 (`lisinopril|egfr<60` is in the partition but can't be fetched), and Q08 (EX-001 is an expected note, not a Flag, so `route` never sees it). Q15 and Q17 come back `known` only when the caller passes the asked drug's flags along with `check_all`, which is what the app does. When only `check_all` is passed they are `no_data`. Messages sent to B and D.
- **Class:** Advances
- **Plan:** advances G2, F3, F4, M4, I4
- **Contract impact:** none
- **Affects:** B: nothing to do. The test pins A's side of the handoff, and the offline gap is FYI for B and D to settle. D: the offline-state table is in the message. If B's behaviour is the intended one, `offline_state` for those 10 questions may need a note. C, I: none.
- **Demo impact:** none. S3 and S6 run online, or after a pack sync.
- **Tests:** `make test` exit 0, 395 passed, 6 skipped. `check_ownership.py --range origin/main..HEAD`: ownership ok. `check_network.sh`: network ok.
- **Inbox:** I 1501 (PLAN v1.3, D-029 VLM call): A-012 already codes against it. Integrator 1522 (D-030, G2 support): both tasks done here, and encryption at rest is already dropped. Read D-025 to D-031, B-028 and B-029: no change needed from A.
- **Next:** PR #5 review at G2. Live VLM check on real photos if the human starts Ollama. After that, requests from B, C and D.

### A-017 · 2026-11-08 15:34 · commit `1fd3909` · PLAN v1.3

- **Change:** New `tests/A/test_capture_shared_samples.py` (23 tests). No A code changed. It pins `capture.from_image` against C's shared label set (C-022, to-A 1526), the one set Dhiaa asked for. (1) The seven texts from C's `phone/samples/labels.json` (80bf651) are copied in and run on every branch, through the PNG iTXt path and faked OCR. Each gives exactly the right Drug: aspirin 81, clopidogrel 75, omeprazole 20, simvastatin 40, lisinopril 10, amoxicillin 500, ibuprofen 200. Each flags for Alex like the typed med: aspirin none, clopidogrel X1/X2, omeprazole X2, simvastatin X3, lisinopril X4, ibuprofen X5 ×4 (one per med pair), amoxicillin AL-001. The Amoxil label's "allergic to penicillin" line never becomes a product. (2) The real PNGs in `phone/samples/` (C owns them) are tested when the folder exists, which means on main after C's PR. `labels.json` matches A's expected set. Each PNG gives the right Drug and flags from its `gv:label` text. With the iTXt chunk stripped and no engine, it gives `[]` with no guess (I4). With OCR faked to the label text, it gives the right Drug again.
- **Why:** C asked for it (to-A 1526), and it's Dhiaa's 15:20 item 2 (one shared label set). A drift between C's samples and A's parser now fails in A's tests.
- **Verified against C's real files:** I checked out `phone/samples/` from `origin/agent/C-app-ui` into the A worktree temporarily: 23 passed. I removed the files before committing, so no C path is in the commit.
- **Class:** Advances
- **Plan:** advances F2, F3, M3, S2, I4
- **Contract impact:** none
- **Affects:** C: nothing to do. If you change `labels.json` or a PNG, `tests/A` will flag it (message sent). I: 15 of the new tests skip on main until C's PR lands, then they run. B, D: none.
- **Demo impact:** none (supports S2 photo beat and the S6 Amoxil bonus)
- **Tests:** `make test` exit 0, 403 passed, 21 skipped. `check_ownership.py --range origin/main..HEAD`: ownership ok.
- **Inbox:** C 1526 (shared label set) handled here. Read B-030, B-031 and C-022: no change needed from A. B-030 relies on A's brand mapping (Advil, Prilosec, Protonix, Zestril, Aleve, Bayer), which is noted and unchanged. No new DECISIONS since D-031, and PLAN is still v1.3.
- **Next:** PR #5 review at G2. Live VLM check on C's PNGs with the iTXt stripped, if the human starts Ollama. After that, requests from B, C and D.

### A-018 · 2026-11-08 15:37 · commit `a831312` · PLAN v1.3

- **Change:** New `tests/A/test_app_real_path.py` (9 tests). No A code changed. B's PR #2 and C's PR #3 are on main now, so this is the post-gate switch from mocks to real code (AGENTS.md §11). C's app tests swap A's functions for stand-ins; these don't. They go through C's real FastAPI app with A's real `graph`, `rules`, `normalize` and `capture`, and pin: (1) `/api/status` reports those four modules as `real` and A's extras (`expected_notes_all`, `expected_notes`, `no_data_keys`) as present. (2) `/api/profile` is Alex from `data/` with CYP2D6 `not_assessed` (D-021, D-031). (3) `/api/flags` is exactly X1–X4 on their exact keys, X2 shown once, equal to `rules.check_all(graph.load_profile())`, and no evidence says "safe". (4) The notes are expected-combination keys only and are never also flags. (5) Typing "Advil" gives ibuprofen with X5 on all four keys. (6) "Protonix 40 mg" gives pantoprazole, no flags, and `clopidogrel|pantoprazole` in `no_data` (S6, I4). (7) An unknown name gives nothing, not a guess. (8) `/api/capture/confirm` with simvastatin 40 flags X3, and with 20 it flags nothing. (9) A question naming Advil adds X5 to the flags the app routes (B-025); `route()` is never called.
- **Why:** This is the first time A's real code runs inside the merged app. If the wiring or A's output drifts from P5, the suite now goes red. Only local endpoints are used, so nothing reaches the cloud (I2).
- **Class:** Advances
- **Plan:** advances G2, F2, F3, M4, S2, S6; I4 (no_data, no guess)
- **Contract impact:** none
- **Affects:** C: FYI only, nothing to do. If `app.py` stops resolving A's modules or changes `/api/check`, `/api/flags` or `/api/capture/confirm` output, `tests/A` will flag it. B, D, I: none.
- **Demo impact:** none (pins S2 and S6 on real code)
- **Tests:** `make test` exit 0, 1078 passed, 2 skipped. After rebasing on main (B and C merged), the 15 phone/samples tests from A-017 run instead of skipping. I did not run `check_ownership.py` or `check_network.sh`: both needed approval in this session. The commit touches only `tests/A/`.
- **Inbox:** nothing new for A. No new DECISIONS since D-031, PLAN is still v1.3, and there are no new LOG entries from B, C or D since my last cycle. PR #5 is MERGEABLE, and CI was still running at the time of writing.
- **Next:** PR #5 review. Live VLM check on C's PNGs if the human starts Ollama. After that, requests from B, C and D.

### A-019 · 2026-11-08 15:42 · commit `ad4ee19` (rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #5 onto main (v1.3.1, D-032) and force-pushed it (`ad4ee19`). Then I ran a G3 merge rehearsal in a throwaway worktree: `origin/main` merged with all four open PRs (#4 D, #5 A, #7 B, #8 C) in one octopus merge. It merged with no conflicts, and `make test` exited 0 with 1148 passed and 0 skipped. I removed the worktree afterwards and pushed nothing from it. I also checked every ingredient in A's name table (126) against B's frozen partition v5 (140 keys plus aliases). Every flag key A can fire for Alex is in the universe, except the `allergy:penicillin|*` keys. Those are local-only flags, which B accepted in to-A 1502. B's `test_rule_keys_match_real_rules_when_present` already pins this, so I added no duplicate test.
- **Why:** G3 is at 17:30, and the integrator will merge these four PRs together. Knowing now that they merge cleanly and stay green saves time at the gate.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; I4/I5 (A's keys stay inside the frozen v5 universe, D-027)
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: the four open PRs (#4, #5, #7, #8) merge cleanly together and stay green (message sent). B, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on my rebased branch: exit 0, 1078 passed, 2 skipped. On the integrated main+#4+#5+#7+#8: exit 0, 1148 passed. I did not run `make eval` or `core.cloud check` (they needed approval in this session).
- **Inbox:** to-A 1535 (G2 passed, D-032, v1.3.1): I rebased. to-A 1537 (C-023 recolored PNGs, same text): the A-017 sample tests still pass, and they don't check pixels. New logs: B-033 and C-023, nothing for A.
- **Next:** PR #5 review and merge at G3. Live VLM check on C's PNGs if the human starts Ollama. Then requests from B, C and D. If B ships a partition v6, re-run the key-coverage check.

### A-020 · 2026-11-08 15:50 · commit `83219b9` (rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #5 onto main (now has D-033) and force-pushed it (`83219b9`). Then I re-ran the G3 merge rehearsal on the newest PR heads, because B (#7 → `0163ba9`) and C (#8 → `ff5a93c`, mock fallbacks dropped in C-024) had both pushed since A-019. In a throwaway worktree I octopus-merged `origin/main` (`eceabe8`) with #4 D (`5112526`), #5 A, #7 B and #8 C. There were no conflicts, and `make test` exited 0 with 1154 passed and 0 skipped. Nothing in A's suite skips any more on the integrated tree. That includes A-018's app real-path tests, which now run on C's app with no stand-ins. I removed the worktree and pushed nothing from it.
- **Why:** G3 is at 17:30. Two of the four PRs changed after the last rehearsal, so the A-019 result was out of date.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: the four open PRs still merge cleanly together and stay green on their current heads (message sent). B, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on my rebased branch: exit 0, 1078 passed, 2 skipped (the 2 skips wait on PR #4 queries.json and C's app path, both fine on the integrated tree). Integrated main + #4/#5/#7/#8: exit 0, 1154 passed, 0 skipped.
- **Inbox:** to-A 1543 (C-024 ack): I noted that `_named_drugs` no longer checks for a mock normalizer, and A's tests don't rely on that. D-033 (Gabe is integrator, backup Dhiaa): noted, nothing for A. New logs: B-034, B-035 and C-024, nothing for A. B-035 confirms Q03 (`CYP2D6:not_assessed|codeine`) stays no_data offline, as A's rules intend (D-021).
- **Next:** PR #5 review and merge at G3. Live VLM check on C's PNGs if the human starts Ollama. Then requests from B, C and D. If B ships partition v6, re-run the key-coverage check.

### A-021 · 2026-11-08 15:50 · commit `d81a2b0` (rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #5 onto main `aa30bbf` (D-034) and force-pushed it (`d81a2b0`). Then I closed the gap the integrator flagged in to-human 1546: the G3 rehearsal had never run `make eval` or `python -m core.cloud check` on the integrated tree. On a local throwaway branch (never pushed, deleted afterwards) I octopus-merged `origin/main` with the current heads #4 D `5112526`, #5 A `d81a2b0`, #7 B `f3a4abc` (B-036) and #8 C `ff5a93c`. There were no conflicts. Results on the integrated tree:
  - `make test`: exit 0, 1156 passed, 0 skipped.
  - `python -m core.cloud check`: 136/136 keys usable, 0 missing, 0 rejected (I7), 0 outside the partition.
  - `make eval DEMO=1` (EVAL_LLM unset, so no API spend): partition `real:data/buckets/v5.json`, backend `live`.
  - `python -m eval.gate`: **20 pass, 0 warn, 0 fail**.
- **Finding for D:** the `slides/numbers.md`, `docs/results.md` and `eval/results/*` committed on PR #4 come from the stand-in partition and the simulated backend. On the integrated build several figures change: random decoys 95%→99%, fixed-bucket repeat-ask 15%→11%, statistical 17%→22% (ceiling 19%→20%), one-session condition guess 75%→72%, separate+cover 29%→34%, blind 27%→26%, **cloud calls 6→11**, **on-device share 75%→50%**, warm offline 17/20→18/20, and a new row: wording filter 25/25. `slides/pitch.md:12` still has the bracketed "[6] cloud calls … [75%] answered on device". Line 10 has "[95%]" and "[14%]". All 20 gate claims still pass. Only the quoted numbers need regenerating after the merge. I discarded my regenerated files and pushed none of them.
- **Why:** G3 is at 17:30. P8 requires every quoted figure to match the merged build (D-034). The rehearsal had not yet checked the eval suite or the demo cache.
- **Class:** Advances
- **Plan:** advances G3/G4 (P9) prep; checks P8 claims, I3, I4, I7, I8 on the integrated build
- **Refinements:** none
- **Contract impact:** none
- **Affects:** D: re-run `DEMO=1 make eval` after #4 merges with the others and refresh the bracketed pitch numbers (message sent). I: the full G3 sequence (test, cloud check, eval, gate) is green on the current heads (message sent). B, C: nothing to do.
- **Demo impact:** none to the beats. The pitch figures on the learning slide change (S-pitch numbers only).
- **Tests:** `make test` on my rebased branch: exit 0, 1078 passed, 2 skipped. Integrated: as above.
- **Inbox:** no new to-A messages. D-034 (submission accepted, personalization described as rule-based): consistent with A's code, since only `core/capture.py` calls a local model. New log B-036: nothing for A.
- **Next:** PR #5 review and merge at G3. After the merge, re-run A's suite on main. Live VLM check if the human starts Ollama. Then requests from B, C and D.

### A-022 · 2026-11-08 16:05 · commit `1349212` (rebase only, no new code) · PLAN v1.3.1

- **Change:** No code changed. I rebased PR #5 onto main `6c35c51` and force-pushed it (`1349212`). B (#7 → `4101ae2`, B-038) and D (#4 → `0598ceb`, D-012) moved their heads after A-021, so I re-ran the G3 rehearsal. In a throwaway worktree (removed afterwards, nothing pushed from it) I octopus-merged `origin/main` `dba1848` with #5 A `1349212`, #7 B `4101ae2`, #8 C `ff5a93c` and #4 D `0598ceb`. There were no conflicts. Results:
  - `make test` on the integrated tree: exit 0, **1157 passed, 0 skipped** (one more than A-021, from B's new test).
  - `make eval DEMO=1` on the integrated tree (EVAL_LLM unset, no API spend): partition `real:data/buckets/v5.json`, backend `live`. The gate section it wrote reads **21 pass, 0 warn, 0 fail**, and P3 shows "demo replay", so DEMO=1 took effect.
  - I did not run `python -m eval.gate` as its own command this time: the sandbox would not let me run it from the throwaway directory. The 21/0/0 above is the gate table that `make eval` wrote into `docs/results.md`.
  - `python -m core.cloud check`: 136/136 keys usable, 0 missing, 0 rejected (I7), 0 outside the partition. I ran it in A's worktree, not the integrated one. #7 and #8 change no `core/cloud.py` or `data/buckets/` file, so the result carries over.
- **Why:** G3 is at 17:30 and two PR heads changed after A-021. The integrator should merge heads that have been checked together.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; checks I3, I4, I7 and the P8 claims on the integrated build
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: the four current heads (#4 `0598ceb`, #5 `1349212`, #7 `4101ae2`, #8 `ff5a93c`) merge cleanly and stay green. B, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on A's rebased branch: exit 0, 1078 passed, 2 skipped. Integrated: as above.
- **Inbox:** D 1551 (D will report both readings of offline E4; D's human owner decides): handled, nothing for A. B-038 (router-state reading pinned by `tests/B/test_offline.py`): matches A-016. No new DECISIONS since D-034; PLAN still v1.3.1.
- **Next:** PR #5 review and merge at G3. After the merge, re-run A's suite on main. Live VLM check if the human starts Ollama. Then requests from B, C and D.

### A-023 · 2026-11-08 16:15 · commit `f483847` (rebase only, no new code) · PLAN v1.3.2

- **Change:** No code changed. I rebased PR #5 onto main `48c182d` and force-pushed it (`f483847`, same code as `1349212`). D's PR #4 moved to `4bd66e2` (D-013, new gate check E4d) and B's PR #7 to `079fe75` after A-022, so I re-ran the G3 rehearsal. In a throwaway worktree (removed afterwards, nothing pushed from it) I octopus-merged `origin/main` `c2518bc` (PLAN v1.3.2) with #4 D `4bd66e2`, #5 A `f483847`, #7 B `079fe75` and #8 C `ff5a93c`. There were no conflicts. Results:
  - `make test` on the integrated tree: exit 0, **1158 passed, 0 skipped**.
  - `make eval DEMO=1` on the integrated tree (EVAL_LLM unset, no API spend): partition `real:data/buckets/v5.json`, backend `live`, P3 "demo replay". The gate table it wrote reads **22 pass, 0 warn, 0 fail**, E4d included (strict cold 4/20, synced 18/20; user-visible cold 11/20).
  - I did not run `python -m eval.gate` as its own command (the D-035 G4 command's second half): the sandbox would not run it from the throwaway directory. The 22/0/0 above is the table `make eval` wrote into `docs/results.md`.
- **Why:** G3 is at 17:30 and two PR heads changed after A-022. The integrator should merge heads that have been checked together.
- **Class:** Advances
- **Plan:** advances G3 (P9) prep; checks I3, I4 and the P8 claims on the integrated build; G4 command per D-035
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: the four current heads (#4 `4bd66e2`, #5 `f483847`, #7 `079fe75`, #8 `ff5a93c`) merge cleanly on main `c2518bc` and stay green. B, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on A's rebased branch: exit 0, 1078 passed, 2 skipped. Integrated: as above.
- **Inbox:** D 1600 (A-016 settled: E4 reports both readings, strict cold 4/20 differs on the seven questions A listed): handled, nothing for A. D-035 / PLAN v1.3.2 (G4 command `DEMO=1 make eval && python -m eval.gate`): no effect on A's code. New logs B-039, D-013: nothing for A.
- **Next:** PR #5 review and merge at G3. After the merge, re-run A's suite on main. Live VLM check if the human starts Ollama. Then requests from B, C and D.

### A-024 · 2026-11-08 16:25 · commit `f483847` (no new code, no re-push) · PLAN v1.3.2

- **Change:** No code changed. PR #5 stays at `f483847`. Main has gained only coord commits since then, so I did not re-push and the head others have tested stays put. B's PR #7 moved to `91a39b7` after B-040, so I re-checked the integrated set. Every earlier rehearsal had also left one gap: the standalone `python -m eval.gate` half of the D-035 G4 command. I closed it. On a local temp branch in A's code worktree (deleted afterwards, nothing pushed from it) I octopus-merged main `f51ae85` with #4 D `4bd66e2`, #5 A `f483847`, #7 B `91a39b7` and #8 C `ff5a93c`. There were no conflicts.
  - `make test` on the integrated tree: exit 0, **1158 passed, 0 skipped**.
  - `python -m eval.gate` on its own: **22 pass, 0 warn, 0 fail** (P1 `real:data/buckets/v5.json`, P2 live, P3 demo replay, E4d strict cold 4/20 / synced 18/20, I7b 25/25).
  - Not run: `DEMO=1 make eval`. The sandbox refused it this time, so the gate read the `eval/results/*` committed on #4 and did not regenerate them on this tree. The integrator should still run the full D-035 command on main after G3.
- **Why:** G3 is at 17:30. Until now no one had run the gate script on its own against the integrated heads, and B's head had moved again.
- **Class:** Advances
- **Plan:** advances G3/G4 (P9) prep; checks I3, I4, I7 and the P8 claims through the gate; D-035
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: current heads #4 `4bd66e2`, #5 `f483847`, #7 `91a39b7` and #8 `ff5a93c` merge cleanly and stay green, and the gate passes 22/0/0 (message sent). B, C, D: nothing to do.
- **Demo impact:** none
- **Tests:** `make test` on A's branch (rebased locally on `f51ae85`): exit 0, 1078 passed, 2 skipped. Integrated: as above.
- **Inbox:** no new to-A messages. New log B-040 (rehearsal with `1e265c1`, G4 command not run): this entry covers the gate half on B's newer `91a39b7`. No new DECISIONS since D-035; PLAN still v1.3.2.
- **Next:** PR #5 review and merge at G3. After the merge, re-run A's suite on main. Live VLM check if the human starts Ollama. Then requests from B, C and D.

### A-025 · 2026-11-08 16:06 · commit `1b17750` (PR #9) · PLAN v1.3.2

- **Change:** `core/capture.py` now explains why it skipped the local vision model. It logs one line per process per reason on the `genomevault.capture` logger. Model not set: the line says to add `LOCAL_VLM_MODEL=qwen2.5vl:7b` to `.env` (see `.env.example`). Model did not answer: the model name and the exception type only. Reply was not the expected JSON. The level is WARNING under `GV_OCR=vlm`, where the user asked for the model, and DEBUG under `auto`, where running without a model is the normal I8 path. Return values are unchanged (`None` on every skip, as before). The log line never contains label text, image content or exception messages (I2; a test checks this with a synthetic name and Rx number).
- **Why:** to-A 1602 (human, demo laptop): a `.env` without `LOCAL_VLM_MODEL` made `GV_OCR=vlm` return `[]` in 0.0 s with no hint.
- **Class:** Refines
- **Plan:** refines F2, M3, S2 (D-029 setup); I2 and I4 unchanged
- **Refinements:** capture logs a one-time setup hint when the vision model is skipped: WARNING with `GV_OCR=vlm`, DEBUG with `auto`, never label content.
- **Contract impact:** none (`from_image` / `from_text` signatures and return values unchanged)
- **Affects:** C: nothing required. With `GV_OCR=vlm`, C's startup warm-up (C-025) now prints the hint once if the model is unset, so a fast "warm" no longer passes silently. D: nothing required. If the env docs mention `GV_OCR=vlm`, they could add "existing `.env` files need `LOCAL_VLM_MODEL=qwen2.5vl:7b` added by hand". I: please review and merge PR #9.
- **Demo impact:** S2: none on the happy path. With a misconfigured `.env`, the console now says what to fix.
- **Tests:** new `tests/A/test_capture_vlm_hint.py` (6 tests: unset/`set-me` warns once under vlm, quiet under auto, model-down gives type and model only with no label text, bad JSON gives DEBUG and still falls through to tesseract, a good read logs nothing). `make test` on main `52c9634` + this commit: exit 0, **1164 passed**.
- **Inbox:** human 1602 (7/7 real VLM labels, ~4.2 s warm): handled by this change; the untested path from to-human 1523 is closed. Main now has PRs #4, #5, #7 and #8 merged (#5 at `f483847`); my old PR is done, so this change is on new PR #9. New logs B-041 to B-043, C-025, D-014: nothing else for A. No new DECISIONS (D-035), PLAN still v1.3.2.
- **Next:** PR #9 merge. Then the next PLAN version after the G3 ruling, and requests from B, C and D.
