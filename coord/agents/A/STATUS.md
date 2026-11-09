agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-025 capture logs a one-time hint when the local vision model is skipped (LOCAL_VLM_MODEL unset, model down, bad JSON). WARNING under GV_OCR=vlm, DEBUG under auto, never label text. Return values unchanged.
branch: agent/A-data-rules
last_commit: 1b17750
pr: "#9 (open) agent/A-data-rules -> main: A-025 VLM skip hint. Rebased on main 52c9634, make test exit 0, 1164 passed. (#5 merged at G3 as f483847.)"
last_seen:
  plan_version: "1.3.2"
  decisions: D-035
  logs: {A: 25, B: 43, C: 25, D: 14}
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
  - 20261108-1500-from-D-q08-note-counts.md
  - 20261108-1501-from-I-plan-v1-3.md
  - 20261108-1502-from-B-allergy-keys-ok.md
  - 20261108-1510-from-C-allergy-nodata.md
  - 20261108-1516-from-human-skip-encryption.md
  - 20261108-1518-from-D-optional-cases.md
  - 20261108-1522-from-integrator-g2-support.md
  - 20261108-1526-from-C-label-set.md
  - 20261108-1535-from-integrator-g2-passed.md
  - 20261108-1537-from-C-label-pngs-recolored.md
  - 20261108-1543-from-C-app-real-path-ack.md
  - 20261108-1551-from-D-offline-reading.md
  - 20261108-1600-from-D-a016-settled.md
  - 20261108-1602-from-human-vlm-results.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
open_questions: []
notes: >
  A-025: the human's real VLM run (to-A 1602) measured 7/7 labels correct at ~4.2 s each, which closes the
  untested path from to-human 1523. The only issue found was a silent skip when LOCAL_VLM_MODEL was missing from
  .env; A-025 now logs a hint for it. PRs #4, #5, #7 and #8 are merged on main; A's suite on main + A-025:
  1164 passed.
next: >
  PR #9 merge. Then the next PLAN version after the G3 ruling, and requests from B, C and D.
