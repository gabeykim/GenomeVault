agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-033 post-G2 app-path tests (tests/B/test_app_path.py). PR #7 opened (head 71f2d28); make test green. Waiting for review
branch: agent/B-privacy-router
last_commit: 71f2d28
last_seen:
  plan_version: "1.3"
  decisions: D-031
  logs: {A: 17, B: 33, C: 22, D: 11}
handled_messages:
  - 20261108-1310-from-C-ledger-usage.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1331-from-C-check-output-scope.md
  - 20261108-1323-from-D-eval-needs.md
  - 20261108-1352-from-A-x5-keys.md
  - 20261108-1355-from-C-using-extras.md
  - 20261108-1357-from-D-bucket-numbers.md
  - 20261108-1359-from-A-rules-ready.md
  - 20261108-1405-from-D-v2-ack.md
  - 20261108-1404-from-integrator-status-and-cloud-cache.md
  - 20261108-1415-from-D-v3-results.md
  - 20261108-1417-from-A-lab-bands.md
  - 20261108-1425-from-A-phenotype-names.md
  - 20261108-1426-from-D-wording-latency-v4.md
  - 20261108-1428-from-C-status-and-switch.md
  - 20261108-1432-from-C-cover-started.md
  - 20261108-1438-from-D-i4-route-known.md
  - 20261108-1439-from-A-no-data-marker.md
  - 20261108-1444-from-A-universe-names.md
  - 20261108-1500-from-A-allergy-keys.md
  - 20261108-1500-from-D-i4-confirmed.md
  - 20261108-1501-from-I-plan-v1-3.md
  - 20261108-1510-from-C-sync-and-order.md
  - 20261108-1516-from-C-order-handled.md
  - 20261108-1518-from-D-pack-confirmed.md
  - 20261108-1526-from-C-b025-done.md
  - 20261108-1529-from-A-handoff-pinned.md
blocked_on: none
notes: >
  G2: the integrator merged PR #2 (B) and PR #3 (C) into main (be95c0e). My branch had no commits left
  after the rebase. make test on main: exit 0, 789 passed, 3 skipped. With PR #7 it is 794 passed, 3 skipped.
  B-033 adds 5 tests that run B's guarantees (I3, I5, I7, F5, F6, F8) through C's real /api/ask,
  /api/ledger/{seq}/outbound and /api/offline. Message sent to C. PLAN still v1.3, DECISIONS still D-031, nothing new in my inbox.
  LOG numbering: B-031 and B-032 were status-only reports with no LOG entry, so this entry is B-033.
  The allergy test in tests/B/test_g2_real_rules.py still skips until PR #5 (A) merges.
  The untracked Finder copies ("core/cloud 2.py" etc.) are still local only. A human can delete them.
next: PR #7 review. After PR #5 merges, confirm the allergy test runs. After PR #4 (D) merges, run eval/queries.json through the app path
