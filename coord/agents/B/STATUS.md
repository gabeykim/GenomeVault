agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-036 app-path tests fail loudly instead of skipping (getattr on LEDGER_IS_MOCK for C PR #8). PR #7 head f3a4abc, waiting for review
branch: agent/B-privacy-router
last_commit: f3a4abc
last_seen:
  plan_version: "1.3.1"
  decisions: D-033
  logs: {A: 19, B: 36, C: 24, D: 11}
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
  - 20261108-1535-from-integrator-g2-passed.md
  - 20261108-1543-from-C-stand-ins-gone.md
blocked_on: none
notes: >
  G2 passed (D-032, PLAN v1.3.1). BRIEF queue items 1 to 9 are all on main since PR #2.
  B-035: D's eval (PR #4) over main + PR #7 with DEMO=1 gives G4 gate 20/0/0, 11 cloud calls for 20 questions,
  0 personal fields, offline warm/synced 18/20. Without DEMO=1 the live run is silently offline (D told).
  PR #7 is tests only: B-033 (app-path I3, ledger view, offline) and B-034 (knowledge pack through
  /api/sync: whole partition once, I3 on every pack row, pack label, mine=[], offline answers at 0 bytes,
  409 while offline). B-036: app-path tests now assert the real router/ledger/pack instead of skipping. make test exit 0, 801 passed, 3 skipped. Ownership check ok.
  The allergy test in tests/B/test_g2_real_rules.py still skips until PR #5 (A) merges.
  The untracked Finder copies ("core/cloud 2.py" etc.) are still local only. A human can delete them.
next: PR #7 review before G3 (17:30). After PR #5 merges, confirm the allergy test runs. After PR #4 (D) merges, re-run DEMO=1 make eval on main
