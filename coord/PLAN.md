# GenomeVault PLAN — v1.3.5

Source of truth for the idea. Edited only by the integrator, through accepted proposals (see AGENTS.md §5, §12). Cite these IDs in every commit, report and proposal.

## P1 Goal

A personal health agent that keeps genome, records and bloodwork on the user's device, checks any new medication against them locally, and borrows cloud intelligence without the cloud learning who the user is or what they have. Cloud answers are stored locally, so the agent needs the cloud less over time.

Pitch: *Your genome never leaves your device. The cloud never learns what you asked. And the more you use it, the less it needs the cloud.*

Event fit: Lenovo × AGI House hybrid AI build day (personal context on device, cloud only when needed, cross-device, offline, compliance).

## P2 Features

| ID | Feature | Priority |
| --- | --- | --- |
| F1 | Personal health graph (genotypes → phenotypes, meds, conditions, allergies, dated labs) | Must |
| F2 | Input capture: label photo, typed/voice drug name, OTC/supplement | Must |
| F3 | Local cross-reference engine: gene–drug, drug–drug, drug–lab, allergy | Must |
| F4 | Privacy router (P6) | Must |
| F5 | Ledger of everything that left the device | Must |
| F6 | Learning knowledge base (stores all cloud answers, decoys included), plus a knowledge pack: the whole fixed partition recorded once for every user (`mocks/cloud_cache/`), loaded by `router.sync_pack()` (D-027) | Should |
| F7 | Actions: pharmacist draft, visit summary, reminders to phone | Should |
| F8 | Offline mode | Should |

## P3 Architecture

| ID | Module | Owner |
| --- | --- | --- |
| M1 | ingest (VCF, records, labs → graph) | A |
| M2 | graph (SQLite, lab staleness) | A |
| M3 | capture + normalize (OCR, brand → ingredient) | A |
| M4 | rules engine → Flags | A |
| M5 | router, generalize, decoys, validator | B |
| M6 | knowledge base (exact key, tiers, expiry) | B |
| M7 | ledger | B |
| M8 | cloud client (only networked module in the app) | B |
| M9 | merge + actions | C |
| M10 | UI, phone page, demo mode | C |
| M11 | evaluation, slides, docs | D |
| M12 | contracts, interfaces, local LLM client, mocks | I |

Flow: phone → capture → rules (reads graph) → router → KB exact-key hit? → else bucket → cloud → store all answers in KB → merge → actions → phone. The ledger logs every outbound byte.

## P4 Invariants (never weakened without a proposal and human approval)

- **I1** All patient data is synthetic.
- **I2** In the app (`core/`, `app.py`, `ui/`, `phone/`), only `core/cloud.py` makes outbound network calls; `core/local_llm.py` may talk to localhost only. `eval/` calls models only via `eval/llm_client.py`.
- **I3** Zero personal fields in any outbound text; the leakage check blocks the send.
- **I4** Exact-key facts only. No extrapolation between drugs. Missing key = `no_data`. Class-level rules only as authored entries with a source.
- **I5** Decoy buckets are a fixed, versioned partition (k = 8). Every member maps to the same bucket. Never generate decoys from the real query.
- **I6** Trust tiers: high-severity flags require a `curated` fact; `cloud` facts are labeled "AI-summarized, verify" and expire sooner.
- **I7** Never output "safe". Outputs prepare the user for a pharmacist or doctor; never start/stop instructions.
- **I8** The full demo runs in demo mode with no network.

## P5 Data: Alex (synthetic)

| Category | Values |
| --- | --- |
| Situation | 58, just discharged after a coronary stent |
| Conditions | CAD, hypertension, high cholesterol, GERD |
| Allergy | Penicillin |
| Genotypes | CYP2C19 \*2/\*2 (poor metabolizer); SLCO1B1 \*1/\*5 (decreased); CYP2D6 not_assessed (gene deletions/duplications are not callable from SNP data; no rule may use it); CYP2C9 \*1/\*1; VKORC1 reference |
| Labs | eGFR 48 (62 a year ago); K 5.2 mmol/L; ALT 28; CK 110; LDL 142 |
| Meds | aspirin 81, clopidogrel 75, omeprazole 20, simvastatin 40, lisinopril 10 |
| Later input | ibuprofen (offline beat) |

Expected flags: **X1** clopidogrel × CYP2C19 PM (high) · **X2** omeprazole × clopidogrel × CYP2C19 (high) · **X3** simvastatin 40 × SLCO1B1 decreased (medium, dose-conditioned) · **X4** lisinopril × K/eGFR trend (medium) · **X5** ibuprofen × antiplatelets and × lisinopril/eGFR (high).
Deliberately absent from curated tables: `clopidogrel|pantoprazole` (demo of no-extrapolation, S6).
Expected therapy, no Flag (informational UI note only): `aspirin|clopidogrel` is standard dual antiplatelet therapy after a coronary stent — A records expected combinations in `data/rules/expected_combinations.json`; the NSAID + antiplatelet rule (X5) still fires for `ibuprofen`. Genotypes are matched by rsID (the VCF `ID` column), never by position; VCF coordinates are GRCh38 per dbSNP (rs4244285 `CYP2C19*2` chr10:94781859; rs4986893 `*3` chr10:94780653; rs12248560 `*17` chr10:94761900).

## P6 Privacy stack (in order)

1. Local rules answer it → nothing sent.
2. KB exact-key hit, not expired → nothing sent.
3. Generalize: all phenotypes / all lab bands; strip every personal field.
4. Split: one concept per request; separate sessions; randomized delays.
5. Bucket: send the key's fixed bucket of 8; store all 8 answers.
6. Cover traffic: cover buckets on a steady schedule.
7. Leakage check on outbound text (I3).
8. Ledger entry.

Knowledge pack (D-027): the entire fixed partition, asked once with the same generalized questions for every user and human-reviewed, ships as `mocks/cloud_cache/`. `router.sync_pack()` loads it into the KB, so a synced question stops at step 2 and sends nothing. Steps 3–8 remain for keys not yet synced and for the cold-start demo beat (S4).

Adaptive questions (D-040): a typed drug name that matches no exact key gets a suggestion (assumed with an undo when unambiguous; otherwise did-you-mean choices; look-alike names always ask) before any lookup. A key outside the core partition but inside the long-tail partition `data/buckets/tail-v1.json` (fixed, versioned, k = 8, same for every user) goes through steps 2–8 like any other key. A term in neither gets `no_data`, plus an optional consented single send logged as not hidden. All behind flags (`GV_FUZZY`, `GV_TAIL`, `GV_DEMO_LIVE_FALLBACK`).

Answer states: `known` · `none_listed` (exact pair listed as no interaction in a curated source) · `no_data`.

## P7 Evaluation

- **E1** Red team, 50 trials (20 if short on time): naive · random decoys · fixed buckets; plus joint-inference attacker and statistical attacker with frequency priors. Target: fixed buckets ≈ 1/8.
- **E2** Learning curve over 20 scripted questions (cloud calls per question, share answered locally).
- **E3** Latency, cloud tokens, answer quality (1–5): local-only vs cloud-only vs hybrid.
- **E4** Offline: questions answered with Wi-Fi off, cold vs warm KB.

## P8 Demo beats

S1 Hook · S2 Capture on phone · S3 Local flags X1–X4, "0 bytes sent" · S4 Hybrid question, buckets in ledger · S5 Red-team chart · S6 Learns (KB hit), no-extrapolation (pantoprazole), offline ibuprofen X5, actions to phone · S7 Close with learning curve and vision.

## P9 Gates (hours from start; start 12:00)

| Gate | Time | Clock time | Must be true |
| --- | --- | --- | --- |
| G0 | 0:30 | 12:30 | Contracts, interfaces, mocks, protocol on `main` |
| G1 | 2:30 | 14:30 | A merged; X1–X4 fire from real data |
| G2 | 4:00 | 16:00 | B + minimal C merged; one question end to end with live ledger |
| G3 | 5:30 | 17:30 | KB + knowledge pack, full UI, phone page merged (cover traffic if ready) |
| G4 | 6:15 | 18:15 | D's evals run on the integrated build; charts in slides. Gate command: `DEMO=1 make eval && python -m eval.gate` (D-035) |
| G5 | 6:30 | 18:30 | Freeze: bug fixes only; record backup video |
| Draft | 7:00 | 19:00 | Project draft saved on the AGI House page (finalists are chosen from it); demos at 20:00 |

## P10 Open questions (integrator resolves)

- Local model: resolved for the demo laptop (D-028, D-029): Ollama, text `qwen3:8b` with thinking off, vision `qwen2.5vl:7b` for label photos. Lenovo NPU runtime still open.
- Event schedule: resolved (D-025).

## Changelog

- v1.0 — initial plan.
- v1.1 — P9: added clock times for a 12:00 start (D-011).
- v1.2 — P5 PGx corrections: CYP2D6 not_assessed (SNP-uncallable); `aspirin|clopidogrel` expected DAPT shown as an informational note, not a Flag; genotypes matched by rsID on GRCh38. CONTRACTS +`capture.from_image` (A) +`cloud.status` (B). `anthropic` added for the eval LLM client. Backup-integrator pass (D-014…D-021).
- v1.2.1 — G1 passed: A merged (PR #1, merge commit 7af15bf); real `rules.check` fires X1–X4 on Alex's discharge meds and X5 for ibuprofen (D-022).
- v1.3 — P9 gates compressed to the 19:00 draft deadline (D-025); cloud thinking/max_tokens bug and fix (D-026); knowledge pack over partition v5, v5 frozen (D-027); local text model with thinking off (D-028); local vision model for label photos (D-029).
- v1.3.1 — G2 passed: B (PR #2, merge 9d04dcc) and C (PR #3, merge be95c0e) merged; real `router.route` + `ledger` + cloud cache replay + FastAPI UI on main (D-032).
- v1.3.2 — P9 G4: gate command fixed as `DEMO=1 make eval && python -m eval.gate`; without DEMO=1 and no key, E2/E4 understate the design and gate check P3 fails (D-035).
- v1.3.3 — G3 passed: A (#5, 61f94d4), B (#7, 1ceb00a), C (#8, e15cbcc), D (#4, 87d6e0a) merged; KB + knowledge pack, full UI, phone page, offline/sync, and E1–E4 evals on main (D-036).
- v1.3.4 — G4 passed: `DEMO=1 make eval && python -m eval.gate` green on the integrated build (22 pass, 0 fail) (D-038).
- v1.3.5 — Adaptive questions accepted (D-040): typo suggestions, long-tail fixed partition, demo live fallback, consent path; all behind flags, ON only if green by 18:00.
