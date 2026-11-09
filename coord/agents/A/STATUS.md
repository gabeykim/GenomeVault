agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: Holding for the G5 freeze. PR #18 (tests only) at e34e618. The D-043 merge order (#22, #20, #18, #21, #19, #23) was rehearsed with make test exit 0, 1335 passed, both with all five flags unset and with all five set. BRIEF queue 1-8 and D-040 part 1 done.
branch: agent/A-data-rules
last_commit: e34e618 (PR head; local rebase 8aaf3ab on main 27a14fb, no code diff, not re-pushed)
pr: "#18 open (tests only). #17, #9 merged."
last_seen:
  plan_version: "1.3.7"
  decisions: D-043
  logs: {A: 38, B: 74, C: 31, D: 19}
  proposals_seen: [20261108-1655-human-adaptive-questions.md]
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
  - 20261108-1605-from-integrator-g3-passed.md
  - 20261108-1610-from-integrator-pr9.md
  - 20261108-1611-from-C-vlm-configured.md
  - 20261108-1617-from-D-env-line.md
  - 20261108-1638-from-integrator-g4-passed.md
  - 20261108-1658-from-integrator-adaptive-questions-pending.md
  - 20261108-1702-from-I-adaptive-part1.md
  - 20261108-1702-from-C-suggest-shape.md
  - 20261108-1710-from-I-suggest-sound-alikes.md
  - 20261108-1708-from-C-d040-ui-ready.md
  - 20261108-1709-from-integrator-d041-suggest-contract.md
  - 20261108-1717-from-D-typo-results.md
  - 20261108-1731-from-C-swap-fixed.md
  - 20261108-1734-from-B-new-keys-need-partition.md
  - 20261108-1745-from-I-adaptive-on.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
  - "Stretch: PharmCAT path. Needs a new external dependency (Java tool), a human ask under AGENTS §9, and G4 says hold new code."
open_questions: []
notes: >
  17:41 cycle (A-038): coord-only moves on main (A-037, B-074). Rebased, make test exit 0 (1297 passed, 1 skipped, 1 xfailed). No new inbox, DECISIONS, proposals, FREEZE or STOP.
  B-074's DEMO=0 finding is in integrator-owned tests/I/; nothing for A.
  17:39 cycle: D-043 flags checked set and unset (A-037). A adds no rules before the freeze (to-A 1734).
next: >
  Hold PR #18 for Gabe's merge in the D-043 order. Demo-critical fixes only. Then hold for the G5 freeze (18:30).
