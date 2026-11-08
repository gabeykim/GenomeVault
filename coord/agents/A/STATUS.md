agent: A
state: working     # working | blocked | waiting-review | done | not-started
current_task: queue 5 (ingest + graph) next; PR #1 ready for G1 merge (now includes D-021 corrections)
branch: agent/A-data-rules
last_commit: 3ce9f6d
pr: "#1 (ready) agent/A-data-rules -> main: queue 1-4 + D-021 PGx corrections + expected_combinations"
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 4, B: 13, C: 10, D: 6}
handled_messages:
  - 20261108-1310-from-C-typed-input.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1324-from-B-bucket-keys.md
  - 20261108-1404-from-integrator-pgx-and-capture.md
  - 20261108-1405-from-D-dedupe-ack.md
  - 20261108-1408-from-B-rule-keys-covered.md
  - 20261108-1410-from-B-v2-lab-bands.md
blocked_on: none
notes: >
  A-004: D-021 done. CYP2D6 not_assessed and guarded in the engine; aspirin|clopidogrel is
  expected_combinations EX-001 (rules.expected_notes, never a Flag); VCF *3 at GRCh38 94780653,
  unverified positions marked. Asked the integrator to update mocks/alex_profile.json for CYP2D6, and
  warned C about tests/C/test_actions.py:56. No new rule keys (B's guard test unaffected).
next: queue 5 (ingest.py VCF by rsID -> phenotypes, CYP2D6 not_assessed; graph.py load_profile + stale labs), then 6 (capture.from_image, D-020), 7, 8
