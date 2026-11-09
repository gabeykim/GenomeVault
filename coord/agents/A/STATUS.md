agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: D-040 part 1, normalize.suggest behind GV_FUZZY (off by default). Built, tests green, PR #17 open for review. BRIEF queue 1-8 done.
branch: agent/A-data-rules
last_commit: e790cb4 (on main 6e3b20d)
pr: "#17 open (D-040 part 1). #9 merged."
last_seen:
  plan_version: "1.3.5"
  decisions: D-040
  logs: {A: 32, B: 64, C: 28, D: 16}
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
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
  - "Stretch: PharmCAT path. Needs a new external dependency (Java tool), a human ask under AGENTS §9, and G4 says hold new code."
open_questions:
  - "Is GV_FUZZY ON for the demo? Integrator decides at 18:00, once C's part 4 renders it (to-integrator 1706)."
notes: >
  This cycle: D-040 accepted the adaptive-questions proposal, so PLAN is now v1.3.5. That supersedes the 1658 hold.
  A built part 1, commit e2dc7a3 and PR #17. It adds core/normalize.suggest, data/rules/lookalikes.json (27 groups) and tests/A/test_suggest.py (+42 tests).
  make test exit 0, 1219 passed. With the flag off, nothing changes. to_ingredients is unchanged, so I4 holds.
  Messages sent: to-C 1706 (the final return shape), to-D 1706 (typo set for part 5), to-integrator 1706 (PR ready).
  C's to-A 1702 crossed with A's 1706. A then added `term` and `assumed` keys (e790cb4, A-032), so C's planned reader works as is. Reply sent: to-C 1712.
  Final shape: {token, term, span, mode, assumed, choices, not_covered}.
  No FREEZE, no STOP.
next: >
  Answer C and D if they need a field or change, before 17:45. Rebase PR #17 if main moves.
  If PR #17 isn't merged by 18:00, the flag stays off. After that, hold for the G5 freeze (18:30).
