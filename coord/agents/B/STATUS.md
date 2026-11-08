agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-030 brand-name question tests done. PR #2 rebased on main 0cf2180, head 28e5edf, waiting for G2
branch: agent/B-privacy-router
last_commit: 28e5edf
last_seen:
  plan_version: "1.3"
  decisions: D-031
  logs: {A: 15, B: 30, C: 22, D: 11}
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
blocked_on: none
notes: >
  Rebased onto main 0cf2180 (D-030, D-031). make test exit 0: 658 passed, 1 skipped.
  New tests/B/test_brand_questions.py (21 tests) runs on A's real normalizer: brand names map to ingredient keys and never leave the device.
  The one skip left is tests/B/test_g2_real_rules.py, which waits for A's allergy engine (PR #5).
  BRIEF queue items 1-9 and the stretch item are done.
  The untracked Finder copies ("core/cloud 2.py", "... 4.py" etc.) are still local only and not committed. A human can delete them.
next: G2 merge of PR #2. After PR #5 merges, rebase and confirm the allergy test in test_g2_real_rules runs instead of skipping
