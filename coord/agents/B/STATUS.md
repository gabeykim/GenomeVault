agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-048 PR #10 rebased onto 16dbc59 (6dc7f25), 1160 passed
branch: agent/B-privacy-router
last_commit: 6dc7f25
last_seen:
  plan_version: "1.3.3"
  decisions: D-037
  logs: {A: 28, B: 48, C: 26, D: 15}
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
  - 20261108-1551-from-D-p3-added.md
  - 20261108-1600-from-D-strict-reading.md
  - 20261108-1605-from-integrator-g3-passed.md
  - 20261108-1617-from-D-sync-line.md
blocked_on: none
notes: >
  G2 passed (D-032, PLAN v1.3.1). BRIEF queue items 1 to 9 are all on main since PR #2.
  B-035: D's eval (PR #4) over main + PR #7 with DEMO=1 gives G4 gate 20/0/0, 11 cloud calls for 20 questions,
  0 personal fields, offline warm/synced 18/20. Without DEMO=1 the live run is silently offline (D told).
  PR #7 is tests only: B-033 (app-path I3, ledger view, offline) and B-034 (knowledge pack through
  /api/sync: whole partition once, I3 on every pack row, pack label, mine=[], offline answers at 0 bytes,
  409 while offline). B-036: app-path tests now assert the real router/ledger/pack instead of skipping. make test exit 0, 801 passed, 3 skipped. Ownership check ok.
  The allergy test in tests/B/test_g2_real_rules.py skips on PR #7 alone. In a throwaway merge with PR #5 it runs and passes
  (B-037: 1090 passed, 2 skipped, exit 0).
  B-039: octopus merge of main dba1848 + PR #7, #8 (ff5a93c), #5 (1349212), #4 (0598ceb): no conflicts, make test exit 0, 1157 passed, 0 skipped. Integrator told.
  B-038: offline + covering flag + cold KB = no_data (I4), pinned by test_offline_cold_kb_is_no_data_zero_bytes_no_ledger; D told for E4 two-reading report.
  B-040: rehearsal re-run on the moved heads (#5 f483847, #4 4bd66e2): 1158 passed, 0 skipped, exit 0. The D-035 G4 command
  was not run because the sandbox refused make eval. Integrator asked to run it on main.
  B-041: rebase only onto f51ae85 (coord-only changes on main since B-040), head 91a39b7, PR CI green. A-023 confirms the same code set green (1158, gate 22/0/0).
  B-042: rebase only onto 0ed2e0c (one integrator inbox commit to A, C, D, nothing for B), head e269240, make test exit 0, 801 passed, 3 skipped.
  B-043: PR #7 merged (1ceb00a) with #5, #8, #4 (main 87d6e0a). Branch now equals main. make test exit 0, 1158 passed, 0 skipped.
  `make eval DEMO=1` + `python -m eval.gate` on main: G4 gate 22 pass, 0 warn, 0 fail. Generated docs/eval files reverted, not committed.
  The untracked Finder copies ("core/cloud 2.py" etc.) are still local only. A human can delete them.
  B-044: G3 passed (D-036, PLAN v1.3.3), nothing changes for B. PR #10 (tests only, d74c0b5) explains C-025's one-group Sync:
  in DEMO=1, offline=true comes only from a forced offline switch (S6 Wi-Fi off pressed during a ~2 min stage-delay Sync).
  Sent groups are kept, and the next sync resumes. C and D told. make test exit 0, 1160 passed.
  B-045: PR #10 rebased onto main c673542 (head 82032ff), make test exit 0, 1160 passed. Throwaway merge of main + PR #9 (A-025) + PR #10:
  no conflicts, exit 0, 1166 passed. Integrator told.
  B-046: PR #10 rebased onto main 8946465 (head f8c7fe1), make test exit 0, 1160 passed. Throwaway merge of main + #9 (cf3df82)
  + #10 (f8c7fe1) + #11 (ad4300f) + #12 (3fcab5a, draft): no conflicts, exit 0, 1171 passed. Integrator told.
  B-047: PR #10 rebased onto main 565cbcb (coord-only changes), head b1a94ad, make test exit 0, 1160 passed.
  B-048: PR #10 rebased onto main 16dbc59 (coord-only changes), head 6dc7f25, make test exit 0, 1160 passed. D-015 put the S6 sync-before-Wi-Fi-off step in the script.
next: PR #10 for the integrator before G4 (18:15). Then answer inbox requests until G5 freeze
