agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: D-040 part 1 done (suggest behind GV_FUZZY, shape frozen by D-041). This cycle added a test-only check of how C swaps a suggestion into the text, and found a hyphen gap in C's _swap. PR #17 open for review. BRIEF queue 1-8 done.
branch: agent/A-data-rules
last_commit: 7bde586 (on main 7853af4)
pr: "#17 open (D-040 part 1). #9 merged."
last_seen:
  plan_version: "1.3.6"
  decisions: D-041
  logs: {A: 34, B: 65, C: 30, D: 16}
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
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
  - "Stretch: PharmCAT path. Needs a new external dependency (Java tool), a human ask under AGENTS §9, and G4 says hold new code."
open_questions:
  - "Is GV_FUZZY ON for the demo? Integrator decides at 18:00, once C's part 4 renders it (to-integrator 1706)."
notes: >
  This cycle: read D-041 (PLAN v1.3.6), which makes the suggest() shape a contract (no key changes until freeze), and C's to-A 1708.
  Added tests/A/test_suggest_swap.py (4 tests, test-only, normalize.py unchanged). It checks that span indexes the typed text,
  that term is the typed word lowercased, and that swapping assumed in makes to_ingredients find the meant drug.
  Found a gap: C's _swap regex (?<![\w-]) skips parts of hyphenated combos (lisinoprl-hydrochlorothiazide), so the banner
  would claim lisinopril while the check ran without it. Told C to swap by span (to-C 1720). Commit 7bde586, A-034.
  make test exit 0, 1234 passed. No FREEZE, no STOP.
next: >
  Hold PR #17 for review. If C changes _swap, update the copy in test_suggest_swap.py.
  18:00: the integrator rules on GV_FUZZY. If PR #17 isn't merged by then, the flag stays off. Then hold for the G5 freeze (18:30).
