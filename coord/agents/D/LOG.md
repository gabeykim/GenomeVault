# Agent D — impact log (append only)

Entries use coord/templates/impact-report.md and are numbered D-001, D-002, ...

### D-001 · 2026-11-08 13:23 · commit `bd8e949` · PLAN v1.1

- **Change:** `eval/queries.json` (20 scripted questions: 5 gene–drug, 5 drug–drug, 4 drug–lab, 3 OTC, 3 open-ended) with exact local keys, generalized topic keys, expected flags/states, offline state, demo beat and a reference answer each. `eval/fixtures/universe_v1.json` (64 generalized keys, documented synthetic priors, domains, co-prescription clusters) and a fixed 8×8 stand-in partition `eval/fixtures/buckets_v1.json`. `eval/universe.py` loads B's `data/buckets/v1.json` first when it exists.
- **Why:** BRIEF D item 1: questions written before B's router lands so the eval is honest.
- **Class:** Refines
- **Plan:** advances P7 (E1–E4 inputs), M11; refines P6.3
- **Refinements:** (1) Generalized topic key form: gene–drug `GENE|drug` (phenotype dropped), drug pair `pair_key(a,b)`, drug–lab `drug|lab` (threshold and dose dropped), e.g. `CYP2C19:poor_metabolizer|clopidogrel` → `CYP2C19|clopidogrel`, `lisinopril|potassium>5.0` → `lisinopril|potassium`. (2) Out-of-universe pairs (Q09 lisinopril|simvastatin, Q16 St. John's wort) are expected to send nothing and return `no_data` (I5). (3) Q17 naproxen is expected to be answered by an authored NSAID class rule.
- **Contract impact:** none
- **Affects:** B: D's evals assume the topic-key form above; the stand-in universe is a suggestion for `data/buckets/v1.json` → reply if your key form differs (message sent). A: D expects the phenotype strings A-001 fixed → none.
- **Demo impact:** none (S3/S4/S6 questions are Q01, Q02, Q06, Q11, Q18, Q19, Q15, Q07)
- **Tests:** `make test` → exit 0
- **Next:** queue item 2

### D-002 · 2026-11-08 13:23 · commit `3d5c460` · PLAN v1.1

- **Change:** E1 red team: `eval/redteam.py`, `transport.py` (simulated wire for naive / random decoys / fixed buckets, separate sessions, cover), `attackers.py` (repeat-ask, statistical, Bayesian joint-inference, optional LLM), `synth.py` (synthetic patients), `llm_client.py` (only model caller in `eval/`, lazy `anthropic` import, replay cache), `charts.py` (dependency-free SVG). Charts in `docs/charts/redteam.svg`, `joint.svg`.
- **Why:** BRIEF D items 2–3.
- **Class:** Refines
- **Plan:** advances P7 E1, M11; checks D-003, D-006; refines P7 E1
- **Refinements:** (1) Deterministic attackers run 500 trials (free; 50 gave ±9-point noise); the LLM attacker keeps the 50-trial budget and runs only with `EVAL_LLM=1`. (2) Joint attacker is Bayesian and knows the public cover rate; "linkable" (same IP) and "unlinkable" (relay) are reported separately. (3) LLM attacker model `EVAL_ATTACKER_MODEL` → `CLOUD_MODEL` → `claude-opus-5-5`.
- **Contract impact:** none
- **Affects:** B: bucket design report in `eval/results/redteam.json` (statistical-attacker ceiling 16% on the stand-in, floor 12.5% needs equal priors inside a bucket) → consider when building `data/buckets/v1.json`. I: `anthropic` SDK dependency request → message sent.
- **Demo impact:** S5 chart exists (simulated): naive 100%, random decoys 95% after 3 asks, fixed buckets 9% (statistical 17%)
- **Tests:** `make test` → exit 0
- **Next:** queue item 4

### D-003 · 2026-11-08 13:23 · commit `a01afe9` · PLAN v1.1

- **Change:** `eval/backends.py` (SimBackend models P6; LiveBackend wraps real rules/router/ledger once importable), `learning_curve.py` (E2), `latency_cost.py` (E3), `offline.py` (E4), `run_all.py` (`make eval` → `docs/results.md` stating partition and backend). `docs/SETUP.md`; `slides/pitch.md`, `demo_script.md`, `judge_qa.md`.
- **Why:** BRIEF D items 4–7, prepared for G4.
- **Class:** Refines
- **Plan:** advances P7 E2–E4, P8, M11; refines P7 E3
- **Refinements:** (1) E3 reports coverage (expected answer state reached) until a judge model scores quality 1–5 on the live build. (2) Latency/tokens are modelled constants in simulated mode, labeled as such.
- **Contract impact:** none
- **Affects:** B: LiveBackend needs a KB reset and an offline switch for cold/warm runs → request sent. C: demo script S4 uses C-002's 8-block visual → none (reply sent).
- **Demo impact:** S6/S7 charts exist (simulated): 6 cloud calls / 20 questions, 70% local, Q19 KB hit; offline 10/20 cold, 18/20 warm
- **Tests:** `make test` → exit 0; `make eval` → ok; `check_ownership.py` → ok; `check_network.sh` → ok
- **Next:** re-run on real flags after G1, live backend after G2; G4 run on the integrated build

### D-004 · 2026-11-08 13:29 · commit `c7e8c6e` · PLAN v1.1

- **Change:** `eval/universe.py` reads B's exact-key `data/buckets/v1.json` (B-001): each member maps to its generalized topic for the evals, the raw-key stats are recorded, and evals fall back to D's stand-in (saying why) when the real partition covers under 25% of D's universe. Fixed `generalize_key` for digit phenotypes (`HLA-B:5701_positive`) and the labs glucose/tsh/magnesium. `docs/results.md` warns when synthetic priors don't cover the partition. `EVAL_BUCKETS=<path>` overrides the file.
- **Why:** B-001 keys buckets by exact local keys. Without this, `make eval` and `tests/D` would have broken as soon as PR #2 merged.
- **Class:** Refines
- **Plan:** advances P7 E1, M11; refines P6.3 (eval-side mapping, consistent with B-002: exact key on device, generalized text outbound)
- **Refinements:** E1 measures recovery of the generalized topic, which is what `Topic.text` reveals per B-002.
- **Contract impact:** none
- **Affects:** B: checked against your file on `agent/B-privacy-router`; all of Alex's topics map, no collisions → none. Only 37 of D's 64 prior keys are in your 96, so D will extend its synthetic priors to your keys before quoting E1 statistical numbers on your partition.
- **Demo impact:** none
- **Tests:** `make test` → exit 0 (34 passed); `make eval` → exit 0; dry run with B's file → all evals run
- **Next:** extend `universe_v1.json` priors/clusters to B's 96 keys; re-run on real flags after G1

### D-005 · 2026-11-08 13:57 · commit `f88da85` · PLAN v1.1

- **Change:** (1) `eval/fixtures/universe_v1.json` v2: synthetic priors, domains and clusters for the 59 keys of B's `data/buckets/v1.json` that D lacked (`src: b-v1`), plus 5 new scenarios. D's stand-in partition still uses D's own 64 keys; it was rebuilt because the cardiac cluster grew. (2) Whether a question's keys can be sent is now computed from the loaded partition (`backends.sendable` / `expected_state`). Q09 is a normal cloud question. (3) E3 coverage is measured against the best answer, so hybrid is charged for keys outside the partition (`not_fully_answered`). (4) `LiveBackend` uses `kb.clear()` and `cloud.set_offline()` (B-008), falls back to `core.interfaces` for rules/graph like C's app, and `offline.py` has a live path. (5) Demo script: C-005 actions plus the calendar-privacy line; C-003 answer format.
- **Why:** B-007/B-008 replies, C-003/C-005/C-007, and the D-004 coverage warning (60 of B's keys had no prior, which inflated the statistical attacker to 38%).
- **Class:** Refines
- **Plan:** advances P7 E1–E4, M11, S6; refines P7 E3 (coverage vs best answer)
- **Refinements:** (1) A question's in-universe status is partition-dependent, never hard-coded. (2) Tests check D's P6 model; live runs are reported, not asserted.
- **Contract impact:** none
- **Affects:** B: per-bucket statistical-attacker numbers on v1 and three keys Alex's questions need → message sent. C: none (reply sent).
- **Demo impact:** S6 line about calendar privacy; S4 read-aloud of the "For you" paragraph
- **Tests:** `make test` → exit 0 (36 passed). Merged locally with `agent/B-privacy-router`: `make test` → exit 0 (331 passed), `make eval` → exit 0 on the live backend (mock rules/graph).
- **Results on B's v1 (simulated wire, full priors):** fixed buckets 12% repeat-ask, 22% statistical (ceiling 23%); joint 71% in one session vs 29–30% with separate sessions + cover (blind guess 30%). Hybrid can't fully answer Q05 or Q14 because their keys aren't in v1.
- **Next:** E3 live latency with and without `GV_DELAY_S` delays; model B-009's uniform cover buckets in E1; G4 run on the integrated build

### D-006 · 2026-11-08 14:05 · commit `eddea32` · PLAN v1.1

- **Change:** Ran the merged A+B+C+D app in demo mode and walked the beats. `slides/demo_script.md`: S6 ibuprofen now goes through "Check another medication" (local rules) instead of the Ask box, S6 Q19 names the 0-byte `kb_hit` row to look for, and a "Before rehearsing" table lists what blocks S4/S6 with owners. `eval/backends.py`: `LiveBackend` dedupes flags by exact key, not id, uses `rules.check_all` when present, and adds `sync_pack()`. `eval/offline.py`: E4 adds a full-pack-sync arm.
- **Why:** Demo walk-through found that every Ask returns `no_data` (empty `mocks/cloud_cache/`), Q19 re-sends b01 + b05 instead of hitting the KB, and the typed ibuprofen check shows one X5 flag instead of four. A-003 flagged the same de-dup bug in D's adapter; B-010 offered `sync_pack()`.
- **Class:** Refines
- **Plan:** advances P8 S4/S6, P7 E4, M11; refines P7 E4 (pack-sync arm)
- **Refinements:** S6's offline ibuprofen beat uses the medication check, not the Ask box.
- **Contract impact:** none
- **Affects:** I: S4 and S6 can't be rehearsed until the demo cache is recorded → message sent. C: the app collapses the four X5 flags into one → message sent. A: de-dup fixed on D's side → reply sent. B: v2 rerun queued → reply sent.
- **Demo impact:** S6 ibuprofen beat moved to the medication check; S4/S6 blocked on the demo cache
- **Tests:** `make test` → exit 0 (38 passed). All four branches merged with this change: `make test` → exit 0 (495 passed). Live E4 on that build: cold 10, warm 10, synced 10, because the empty demo cache leaves nothing to learn.
- **Next:** rerun E1 on B's v2, add priors for v2's four new keys, update `queries.json` lab keys to A/B's banded spelling

### D-007 · 2026-11-08 14:15 · commits `f69dc14`, `0f7b1e3` (merge of main), `4a68768` · PLAN v1.2

- **Change:** `eval/universe.py` follows B's current partition (`core.decoys.CURRENT_VERSION`, else the highest `data/buckets/vN.json`), indexes B's exact keys so a question sends the bucket of its exact local key, and records topics whose phenotype variants sit in different buckets. E1 measures that split. Priors for v2's 4 and v3's 15 new keys (`src: b-v2`/`b-v3`); phenotype variants inherit their topic's prior. `queries.json` q-v3: banded lab keys (`lisinopril|egfr<60`, `simvastatin|alt>120`, `simvastatin|ck>1000`, `ibuprofen|egfr<60`); D-021: Q03 uses `CYP2D6:not_assessed`, Q08 references expected DAPT; synthetic patients carry CYP2D6 not_assessed. Demo script follows C-009's tabs and starts rehearsal with `python -m core.cloud check` (B-013). Merged main (D-014..D-021) into the branch, no rebase.
- **Why:** B-011/B-012/B-013, C-009/C-010, PLAN v1.2 (D-021).
- **Class:** Refines
- **Plan:** advances P7 E1/E3, P8, M11; follows D-021 (P5)
- **Refinements:** (1) The eval partition is B's current version, never a hard-coded file. (2) A topic split across buckets is an E1 leak metric (`phenotype_via_bucket`).
- **Contract impact:** none
- **Affects:** B: v3 puts phenotype variants of two topics in different buckets → message sent (I3). I: same finding, FYI, since it touches an invariant → message sent. C: none.
- **Demo impact:** S3/S4/S6 steps now name C's tabs
- **Tests:** `make test` → exit 0 (42 passed, including main's new contract test). All four branches merged with this change on B's v3: `make test` → exit 0 (548 passed).
- **Results (5 seeds × 1000, synthetic priors):** statistical attacker v1 22.6% ± 2.0, v2 22.1% ± 0.9, v3 20.3% ± 1.5 (v3 ceiling 20.1%); repeat-ask about 12% on all three; joint inference 71% in one session vs 32% with separate sessions + cover (blind guess 25%); v3 genotype revealed by bucket identity 2.4% ± 0.4. Hybrid answers 20/20 on v2 and v3.
- **Next:** E3 live latency with and without `GV_DELAY_S`; adversarial wording cases for B's I7 filter; G4 run on the integrated build

### D-008 · 2026-11-08 14:26 · commits `4f19077`, `928224d` · PLAN v1.2

- **Change:** (1) `eval/wording.py` + `eval/fixtures/wording_cases.json`: 35 adversarial cloud-answer texts (25 that break I7, 8 neutral, 2 rejected by design) scored against B's `validator.wording_problems`. (2) `eval/latency_cost.py`: a live hybrid arm on the integrated build, with `GV_DELAY_S=0,0` and, opt-in via `EVAL_DELAYS=1`, B's default `0.3,2.0`. (3) `queries.json` q-v5: Q01 and Q09 references reworded to pass the I7 rule; Q03 (CYP2D6) is a local `no_data` answer. D's wording test uses B's rule. (4) `universe_v1.json` v5: CYP2D6 topics get prior 0 (D-021: never a real question, so known-fake decoys); synthetic patients never ask a prior-0 topic; priors for v4's four new gene topics. (5) Demo script and judge Q&A: keep demo mode on stage, plus a latency answer.
- **Why:** B-013 asked for adversarial wording cases; E3 live latency was queued; B-014 (v4) and A's D-021 note.
- **Class:** Refines
- **Plan:** advances P7 E1/E3, I7 red team, P8, M11; follows D-021, B-014
- **Refinements:** (1) Prior 0 marks a topic no real user can ask. (2) E3's delayed arm is opt-in because it waits through real P6.4 pauses.
- **Contract impact:** none
- **Affects:** B: wording gaps, delay cost and v4 results → message sent. I: the I7 filter gaps, FYI (invariant) → message sent. A: none (reply sent).
- **Demo impact:** stage run stays in demo mode (live delays add about 19 s to a question that sends buckets)
- **Tests:** `make test` → exit 0 (44 passed, 1 skipped without B's validator). All four branches merged on B's v4: `make test` → exit 0 (636 passed).
- **Results:** I7 filter on the merged build: 3/25 rejected (only the plain cases), 0/5 reassurance without the word, 0/14 rephrased instructions, 0/4 character tricks, 0/1 non-English; 1/8 false alarms. Live E3: median 1.2 ms vs 18.8 s per question that sends buckets (no delay vs default); 0.02 s vs 168 s for the 20 questions. E1 on v4 (5 seeds × 1000): statistical 19.4% ± 0.8, repeat-ask 12.8%, genotype via bucket 1.8% across 4 split topics; joint 76% one session vs 35% separate + cover (blind 26%).
- **Next:** G4 run on the integrated build; extend synthetic patients to A's VCF path (A-005); retake slide screenshots after C-010

### D-009 · 2026-11-08 14:38 · commits `7aaedd3`, `910897c` (merge of main after G1), `a90d87d`, `b76ebc4` · PLAN v1.2.1

- **Change:** G4 prep. (1) `eval/gate.py`: `python -m eval.gate` checks every pitch claim against the results `make eval` wrote, giving PASS/WARN/FAIL and exit 1 on FAIL. Its summary heads `docs/results.md`. (2) `slides/numbers.md`, generated by `make eval`: every figure the pitch and Q&A quote, with its gate status. (3) `docs/G4.md`: the 19:30 runbook. (4) Backends record the local flags and facts behind each answer; a flag answers a question only if its key is one of the question's keys. New gate check I4: no answer may be `known` without a flag or fact covering the question. (5) B's v5 aliases read; priors for v5's four new gene decoys; demo script uses C's Online/Offline switch (C-013) and cover-traffic rows (C-014). (6) Merged main after G1 (D-022); D's evals run against A's real rules.
- **Why:** G4 (19:30) needs the evals run on the integrated build and the charts in the slides, with numbers nobody has to copy by hand. Integrator G1 notice; B-015, B-016; C-013, C-014.
- **Class:** Refines
- **Plan:** advances P9 G4, P7 E1–E4, P8, M11; checks I3, I4, I7
- **Refinements:** (1) The G4 gate is `python -m eval.gate` after `make eval`; FAIL means the claim isn't quoted. (2) A local flag counts as answering a question only when its key is the question's key.
- **Contract impact:** none
- **Affects:** B: I4 finding on `router.route()` → message sent. I: G4 runbook and gate → message sent. C: none (S4/S6 follow C-013/C-014).
- **Demo impact:** S4 cover-traffic line; S6 uses the Online/Offline switch
- **Tests:** `make test` → exit 0 (187 passed with A's modules on main). G4 dry run on a fresh merge of all four branches (B's v5, live): `make test` → exit 0 (720 passed); `make eval` → exit 0; `python -m eval.gate` → 17 pass, 1 warn, 1 fail.
- **Dry-run results:** v5 phenotype splits `{}` (4 aliases); wording filter 25/25 caught, 0/8 false alarms (2 rejected by design); repeat-ask 11%, statistical 22% (ceiling 20%); offline states 20/20 as expected. WARN E2b: the demo cache is unrecorded (`python -m core.cloud check`: 0/136, exit 1). **FAIL I4**: `router.route()` answers `known` ("This was checked on your device… Nothing was sent.") with no flag or fact covering the question for Q03, Q04, Q05, Q16, and for Q13/Q14 where only an unrelated flag (X3) fired.
- **Next:** re-run the G4 gate when B fixes I4 and the cache is recorded; G4 at 19:30

### D-010 · 2026-11-08 15:00 · commits `24e4911`, `7cac7fd` (merge of main), `bc33463` · PLAN v1.2.1

- **Change:** (1) Re-ran the G4 runbook after B-018/B-019 on a fresh merge of A `3b2e4b1`, B `8e98cf1`, C `b4fc781` and D. I4 now passes. (2) `eval/gate.py`: the E2a warning says why on the live build (no recorded demo cache, so repeats go out again); `docs/G4.md` drops I4 from "expected FAIL". (3) Q08: A's curated note EX-001 answers it on the device, so `offline_state` is `known` (`queries.json` q-v7 `local_notes`); both backends count a covering note as backing. (4) Merged main (D-023, D-024).
- **Why:** B fixed the I4 issue D reported (B-018, B-019). A asked whether its EX-001 note should count (A-008).
- **Class:** Refines
- **Plan:** advances P9 G4, P7 E4; checks I4; follows D-021
- **Refinements:** A curated expected-combination note covering a question's exact key counts as local content (like a covering flag).
- **Contract impact:** none
- **Affects:** A: keep `key_state` as it is → reply sent. B: I4 confirmed → reply sent. C: none (palette noted).
- **Demo impact:** none (deck: offline figure now 11/20)
- **Tests:** `make test` → exit 0 (188 passed). Four-branch merge with this change: `make test` → exit 0 (815 passed); `make eval` → exit 0; `python -m eval.gate` → **17 pass, 2 warn, 0 fail** (WARN E2a and E2b: the demo cache is unrecorded, D-019). Offline states 20/20, 11/20 answered cold.
- **Next:** G4 at 19:30 on main once PRs #2–#4 merge; re-check after the demo cache is recorded

### D-011 · 2026-11-08 15:18 · commit `6c1b9d6` · PLAN v1.3 (PR #6)

- **Change:** G4 prep for PLAN v1.3. (1) `eval/offline.py`: the live synced arm called `sync_pack()` while still offline, so B's sync (correctly) fetched nothing; it now goes back online first. (2) `eval/gate.py`: new check E4c, a synced knowledge pack answers offline at least as well as a warm device (D-027). (3) `docs/G4.md`: v1.3 times (G4 18:15, G5 18:30, draft 19:00, demos 20:00), PRs #2–#6, and the pack replaces the expected warnings. (4) `slides/demo_script.md`: S2 with C's phone pairing and "Yes, check it"; S6 in the integrator's order (Q18 twice, Sync knowledge pack, Offline switch, Q07/Q15/Q19, pantoprazole, ibuprofen, Actions) plus the Amoxil allergy bonus; backup video before the 18:30 freeze. Pitch deck re-themed to C's final palette (white third accent), with live learning and offline figures.
- **Why:** PR #6 (D-025 gates, D-027 knowledge pack); B-024, B-025; C-019, C-020.
- **Class:** Refines
- **Plan:** advances P9 G4, P7 E2/E4, P8 S2/S6; follows D-025, D-027
- **Refinements:** E4's synced arm is the D-027 "cold vs synced" split; sync traffic is the whole partition, the same for every user, so it is query-independent by construction (E1's attackers learn nothing from it).
- **Contract impact:** none
- **Affects:** I: G4 is ready on v1.3 → message sent. B: pack confirmed → reply sent. C: S2/S6 follow C-020; the deck matches C-019 → reply sent. A: optional cases queued → reply sent.
- **Demo impact:** S2 and S6 steps rewritten to the integrator's order
- **Tests:** `make test` → exit 0 (188 passed). Dry run on main + PR #6 (`2cc266b`) + A `9e94292` + B `170ba35` + C `714e9b0` + D: `python -m core.cloud check` → exit 0 (136/136 usable); `make test` → exit 0 (916 passed); `make eval` → exit 0; `python -m eval.gate` → **20 pass, 0 warn, 0 fail**.
- **Live results with the pack:** 11 cloud calls for 20 questions (first five 4, last five 0); Q19 answered on the device; offline 11/20 cold, 18/20 warm, 18/20 synced; 0 personal fields; I4 `unbacked_known` empty.
- **Next:** G4 at 18:15 on main per `docs/G4.md`; optional extra cases from A (allergy, look-alike label, label warnings) and B (brand names)

### D-012 · 2026-11-08 15:51 · commits `9b90a78`, `5112526`, `832b065` (merge of main after G2), `0598ceb` · PLAN v1.3.1

- **Change:** (1) `docs/submission.md`: the judging draft (accepted, D-034). (2) `slides/judge_qa.md`: 16 answers on the integrated results, including the integrator's five; `slides/video_script.md`: a 3:00 backup video. (3) Merged main after G2 (D-032): D's branch now runs on A's, B's and C's real modules and the knowledge pack. `eval/results`, `docs/results.md`, `docs/charts` and `slides/numbers.md` come from the live integrated build. (4) New gate check P3 (B-035): a live run must reach the cloud or its demo replay, else FAIL. `docs/G4.md` says to always run `DEMO=1 make eval`.
- **Why:** integrator 15:20 list items 4–6; G2 notice; B-035.
- **Class:** Refines
- **Plan:** advances P8, P9 G2/G4, P7 E2/E4; follows D-025, D-027, D-032, D-034
- **Refinements:** a G4 run without the demo replay or a key is a FAIL, not a quiet understatement.
- **Contract impact:** none
- **Affects:** I: G4 command is `DEMO=1 make eval && python -m eval.gate` → message sent. B: P3 added → reply sent. A: offline-state question is with D's human owner → reply sent. C: deck re-theme to bone/black in progress → reply sent.
- **Demo impact:** none
- **Tests:** on D's branch synced with main: `DEMO=1 make test` → exit 0 (835 passed); `DEMO=1 make eval` → exit 0; `python -m eval.gate` → **21 pass, 0 warn, 0 fail** (P3 FAILs and exits 1 without `DEMO=1`, as intended).
- **Open question (A-016):** B's router answers `no_data` offline for 10 questions where D's E4 counts a covering local flag as answered. D proposes reporting both readings (user-visible content and router state); awaiting D's human owner.
- **Next:** G4 at 18:15; final number pass on deck and submission after G4

### D-013 · 2026-11-08 16:00 · commit `4bd66e2` · PLAN v1.3.1

- **Change:** E4 reports both offline readings (A-016), as decided by D's human owner: **user-visible** (a covering local flag or curated note counts, because it's on screen) and **strict** (only the router's own `known`: a stored fact or a local-only flag). `Result.strict_state`; the simulated backend records what B's router would answer. New gate check E4d. `docs/results.md`, `slides/numbers.md`, `docs/submission.md`, `slides/judge_qa.md` and the deck state both. `slides/pitch.md` bracketed figures are refreshed from the integrated build (A-021).
- **Why:** A-016 question settled; A-021 noted stale pitch figures.
- **Class:** Refines
- **Plan:** advances P7 E4, P8; settles A-016
- **Refinements:** "answered offline" is reported in two readings; neither counts an honest `no_data`.
- **Contract impact:** none
- **Affects:** A: settled → reply sent. B: strict matches `route()` → note sent. I: the submission's offline line now carries both counts → note sent.
- **Demo impact:** none
- **Tests:** `DEMO=1 make test` → exit 0 (836 passed); `DEMO=1 make eval` → exit 0; `python -m eval.gate` → **22 pass, 0 warn, 0 fail**. Offline on the integrated build: user-visible cold 11/20, strict cold 4/20 (Q01, Q06, Q08, Q12, Q18, Q19, Q20 differ); both 18/20 after a pack sync.
- **Next:** G4 at 18:15; final number pass after G4

### D-014 · 2026-11-08 16:07 · commit `3fcab5a` · PLAN v1.3.2

- **Change:** the on-device label-reading result Dhiaa measured (7/7 correct, ~4 s per label, no network; demo set of 7 synthetic printed labels) is now quoted in `slides/numbers.md` under a new "Measured by hand (not from `make eval`)" section, generated from `eval/run_all.MEASURED` so `make eval` keeps it. It is also in `docs/submission.md` (How it works; What's real, and what's demo), `slides/judge_qa.md` (Ollama answer, plus a new label-accuracy question), the S2 line of `slides/demo_script.md`, and the deck's speaker notes for How it works.
- **Why:** to-D/20261108-1602-from-human-vlm-results.md; D's human owner approved.
- **Class:** Advances
- **Plan:** advances P8; D-029
- **Contract impact:** none
- **Affects:** none. The figure is scoped to the demo label set everywhere it appears, as Dhiaa asked.
- **Demo impact:** S2 narration now mentions "about 4 seconds"; no click changes
- **Tests:** `DEMO=1 make test` → exit 0 (836 passed, 2 skipped); `python -m eval.gate` → 22 pass, 0 warn, 0 fail
- **Next:** G4 at 18:15; final number pass after G4

### D-015 · 2026-11-08 16:17 · commit `ec1d49b` · PLAN v1.3.3

- **Change:** `slides/demo_script.md` and `slides/video_script.md` follow C's G3 rehearsal (C-025) and B's note (B-044). S2 starts with `GV_OCR=vlm` and shows the ~4 s "Reading the label on this laptop" step. S4 points at the "Background decoys · N groups · X KB" line (C-023) and says "groups of 8", since Q18 sends 1 or 2; b03's two "yours" rows are noted as correct. S6 shows Sync as one "Knowledge pack · N groups · X KB" line, waits for it to finish before Offline, and syncs off stage when stage delays are on (~2 min). The "Before rehearsing" table is refreshed: the old blockers are done, and the live run with `ANTHROPIC_API_KEY` is still open (Cristian). `docs/SETUP.md` gains the `LOCAL_VLM_MODEL=qwen2.5vl:7b` line for existing `.env` files (A-025). D's branch also merged `main` (v1.3.3, after G3).
- **Why:** to-D 1605 from C, 1606 from A, 1705 from B; D's human owner approved.
- **Class:** Advances
- **Plan:** advances P8 (S2, S4, S6); D-029
- **Contract impact:** none
- **Affects:** none (script and setup wording only)
- **Demo impact:** S2, S4 and S6 wording; no clicks added or removed
- **Tests:** `DEMO=1 make test` → exit 0 (1158 passed) on main merged; `python -m eval.gate` → 22 pass, 0 warn, 0 fail
- **Next:** PR #12 (3fcab5a + ec1d49b) ready once CI is green; G4 at 18:15

### D-016 · 2026-11-08 16:47 · commit `03fe851` · PLAN v1.3.3

- **Change:** final figure pass after G4 (D-038). Re-ran `DEMO=1 make eval` and `python -m eval.gate` on main plus PR #12: **22 pass, 0 warn, 0 fail**, `slides/numbers.md` unchanged, latency moved by under 1 ms. Every figure in the deck, `slides/pitch.md`, `slides/judge_qa.md`, `docs/submission.md` and both scripts matches it. Headers now cite G4 instead of the dry run, and `docs/G4.md` records the result.
- **Why:** to-D/20261108-1638-from-integrator-g4-passed.md asked D to finalize the slide figures; D's human owner approved.
- **Class:** Advances
- **Plan:** advances P7, P8; G4
- **Contract impact:** none
- **Affects:** none
- **Demo impact:** none
- **Tests:** `DEMO=1 make test` → exit 0 (1158 passed); gate 22/0/0
- **Next:** PR #12 merge before G5 (18:30); C's Codespaces link once PR #13 merges and C confirms

### D-017 · 2026-11-08 17:17 · commit `87d818a` · PLAN v1.3.5

- **Change:** D-040 part 5. `eval/fixtures/typo_set.json` is D's own 20-item typo set (Alex's five meds, pack drugs, brands, 8 look-alikes), written independently of A's cases. `eval/adaptive.py` scores A's `suggest()` (correct, silent wrong substitutions, look-alikes assumed) and runs E1's repeat-ask and statistical attackers on B's `tail-v1`. `make eval` appends a separate section to `docs/results.md`. **No gate check and no `slides/numbers.md` figure changes.** Each part reads "Not run" until A's PR #17 and B's PR #15 are on main.
- **Measured** against PR #17 + PR #15: typos **20/20** correct (11 assumed, 9 asked), **0** silent wrong substitutions, **0** look-alikes assumed. Tail: repeat-ask **14%** (near 1 in 8), statistical **59%** (ceiling 58%; 51% with unseen drugs at the median prior), against 22% on the core.
- **Finding (to B):** tail buckets are a seeded shuffle with no frequency balancing, so a bucket often holds one pair with a common drug among rare ones.
- **Why:** to-D 1702 (D-040) and A's, B's and C's 1706–1716 notes; D's human owner approved preparing the parts that are safe whether or not Gabe confirms D-040.
- **Class:** Advances
- **Plan:** advances D-040 part 5 (E1, I4, I5)
- **Contract impact:** none
- **Affects:** B (tail balance finding), A (typo results), I (D-040 confirmation pending; slides unchanged until then)
- **Demo impact:** none
- **Tests:** `DEMO=1 make test` → exit 0 (1181 passed, 2 skipped until #15/#17); gate 22 pass, 0 warn, 0 fail; the 2 skipped tests pass on A's + B's branches
- **Next:** on Gabe's confirmation, the Q&A line and separate slide rows; re-run once #15 and #17 merge

### D-018 · 2026-11-08 17:27 · commit `8d215d1` · PLAN v1.3.6

- **Change:** `slides/presentation_script.md`, the word-for-word presentation script. Version A (about 3:40) interleaves slides 1–4, 7, 9 and 13 with live demo beats S2–S6; Version B (about 2:00) is slides only. Slides 8, 11 and 12 are held for questions, with answers, plus recovery lines if the demo breaks. PR #14 merged before this landed, so it is in PR #21.
- **Why:** D's human owner asked for a full script tied to each slide and demo step.
- **Class:** Advances
- **Plan:** advances P8 (pitch, S1–S7)
- **Contract impact:** none
- **Affects:** none
- **Demo impact:** none (follows C-025 and B-044)
- **Tests:** `DEMO=1 make test` → exit 0 (1291 passed)
- **Next:** PR #21 merge before G5 (18:30)

### D-019 · 2026-11-08 17:33 · commit `606ffca` · PLAN v1.3.6

- **Change:** `eval/adaptive.py` reads `data/buckets/<core.decoys.TAIL_VERSION>.json`, so the tail E1 scores tail-v1 today and tail-v2 as soon as B's PR #20 merges (B-068). `docs/results.md` is re-generated on main now that PRs #15 and #17 are merged. Its closing sentence calls rare questions weaker only when they are.
- **Measured:** on main, typos **20/20**, **0** silent wrong substitutions, **0** look-alikes assumed; tail-v1 statistical **59%**. Checked against PR #20: tail-v2 statistical **15%** (13% with the median prior), repeat-ask **11%**, against 22% on the core.
- **Why:** to-D/20261108-1721-from-B-tail-v2.md; D's human owner approved.
- **Class:** Advances
- **Plan:** advances D-040 part 5 (E1, I5)
- **Contract impact:** none
- **Affects:** B (request done); I (D-040 confirmation still pending; no slide change)
- **Demo impact:** none
- **Tests:** `DEMO=1 make test` → exit 0 (1292 passed); gate 22 pass, 0 warn, 0 fail; `slides/numbers.md` unchanged
- **Next:** PR #21 (script + this) merge before G5; re-run after PR #20 merges
