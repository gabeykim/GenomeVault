agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-009 PharmCAT phenotype-report path (stretch), on PR #5; core queue 1-8 complete
branch: agent/A-data-rules
last_commit: d621bd8
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path. Rebased on origin/main 64b66cb. #1 merged at G1 (D-022)."
last_seen:
  plan_version: "1.2.1"
  decisions: D-024
  logs: {A: 9, B: 18, C: 16, D: 9}
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
blocked_on: none
open_questions:
  - "To D: should the EX-001 DAPT note make aspirin|clopidogrel `known` offline (A now) or `no_data` (Q08)? B-018's router fix may make this moot; D to confirm on re-run."
notes: >
  A-009: ingest can now read a PharmCAT phenotype.json. It is optional and stdlib only; a call is
  used only if it is unambiguous and its phenotype is already in our table; a conflict with the VCF
  or an unknown term gives indeterminate (I4); CYP2D6 stays not_assessed (D-021). Default
  load_profile is unchanged. Read B-018 (router no longer answers known without a covering flag;
  rules.no_data_keys not needed by B), C-015/C-016 (phone page uses capture.from_image; palette),
  D-023/D-024 (loop resilience; Gabe integrator through G2). Last cycle's rebase was not pushed;
  it is now (force-with-lease).
next: >
  PR #5 review at G2. Encryption at rest needs a crypto dependency, so I'd ask the integrator before
  starting. Otherwise: requests from B/C/D.
