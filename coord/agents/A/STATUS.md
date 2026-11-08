agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-008 normalize names for the bucket universe (PR #5); core queue 1-8 complete
branch: agent/A-data-rules
last_commit: f634d24
pr: "#5 (open, checks green at 7cf591f) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names. #1 merged at G1 (D-022)."
last_seen:
  plan_version: "1.2.1"
  decisions: D-022
  logs: {A: 8, B: 17, C: 14, D: 9}
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
blocked_on: none
open_questions:
  - "To D: should the EX-001 DAPT note make aspirin|clopidogrel `known` offline (A now) or `no_data` (Q08)?"
notes: >
  A-008: drug_names.json v2 names all 103 drugs in B's v5 universe (78 were unreadable), plus codeine
  and St. John's wort (st_johns_wort). Names only, no new rules or flags. Read B-017 (G2 test on real
  A rules; says A's queue 8 is blocked, but it is in PR #5) and D-009 (I4 FAIL on router.route; A's
  key_state matches D's offline_state on every key except Q08). Messages sent to B, C, D.
next: >
  Answer D on Q08. Stretch: encryption at rest needs a crypto dependency (stdlib has no cipher, and I
  won't hand-roll one), so I'd raise it with the integrator first. Otherwise: requests from B/C/D.
