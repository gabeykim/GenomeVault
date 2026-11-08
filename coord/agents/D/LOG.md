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
