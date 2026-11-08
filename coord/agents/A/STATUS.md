agent: A
state: working     # working | blocked | waiting-review | done | not-started
current_task: queue 6 (capture.from_image, D-020) next; PR #1 ready for G1 merge (queue 1-5)
branch: agent/A-data-rules
last_commit: bc29bd4
pr: "#1 (ready) agent/A-data-rules -> main: queue 1-5 (data, normalize, rules X1-X5, D-021, ingest + graph)"
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 5, B: 14, C: 11, D: 7}
handled_messages:
  - 20261108-1310-from-C-typed-input.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1324-from-B-bucket-keys.md
  - 20261108-1404-from-integrator-pgx-and-capture.md
  - 20261108-1405-from-D-dedupe-ack.md
  - 20261108-1408-from-B-rule-keys-covered.md
  - 20261108-1410-from-B-v2-lab-bands.md
  - 20261108-1414-from-C-x5-fixed.md
blocked_on: none
notes: >
  A-005: core/ingest.py (VCF by rsID -> diplotype -> CPIC phenotype for the 5 P5 genes, CYP2D6
  not_assessed, uncallable -> indeterminate) and core/graph.py (SQLite; graph.load_profile() per
  CONTRACTS; labs > 90 days old stale; GV_TODAY pins the date, GV_GRAPH_DB picks file storage).
  X1-X4 fire from graph.load_profile(). Read B-014 (v4 buckets; no action for A) and C-011 (X5
  dedupe fixed). Messages sent to C, D, B (FYI), integrator.
next: queue 6 (capture.from_image, D-020), then 7 and 8 (check whether X5 and the no_data marker already cover them, then close)
