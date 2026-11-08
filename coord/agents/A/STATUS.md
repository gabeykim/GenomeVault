agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-010 genotype sweep test (done, on PR #5); core queue 1-8 + PharmCAT stretch complete
branch: agent/A-data-rules
last_commit: 3b2e4b1
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep. Rebased on origin/main 1fb5eee, CI green before this push. #1 merged at G1 (D-022)."
last_seen:
  plan_version: "1.2.1"
  decisions: D-024
  logs: {A: 10, B: 20, C: 16, D: 9}
handled_messages:
  - 20261108-1310-from-C-typed-input.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1324-from-B-bucket-keys.md
  - 20261108-1404-from-integrator-pgx-and-capture.md
  - 20261108-1405-from-D-dedupe-ack.md
  - 20261108-1408-from-B-rule-keys-covered.md
  - 20261108-1410-from-B-v2-lab-bands.md
  - 20261108-1414-from-C-x5-fixed.md
  - 20261108-1426-from-D-re-ingest.md
  - 20261108-1441-from-C-capture-wired.md
blocked_on: "encryption-at-rest stretch: waiting on the human to decide on the `cryptography` dependency (to-human 1454)"
open_questions:
  - "To D: should the EX-001 DAPT note make aspirin|clopidogrel `known` offline (A now) or `no_data` (Q08)? B-018's router fix may make this moot; D to confirm on re-run."
  - "To human: add `cryptography` for encryption at rest, or drop the stretch? (to-human 1454)"
notes: >
  A-010: test-only change. Every SNP genotype combination goes VCF -> ingest -> rules.check. No
  defects found: every rule phenotype is reachable, ingest emits only table phenotypes or
  indeterminate, and gene-drug flags fire exactly for their phenotype and dose band, never for
  indeterminate (I4). Read B-019 (router reads normalize.to_ingredients for brand names; no A
  change) and B-020 (Finder copies; tests/A has none). No new inbox, DECISIONS or PLAN version.
next: >
  PR #5 review at G2. Encryption at rest only if the human approves the dependency. Otherwise:
  requests from B/C/D.
