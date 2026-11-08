agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-026 asked pair leads Answer.facts (170ba35). PR #2 rebased on main 32d4321, waiting for G2
branch: agent/B-privacy-router
last_commit: 170ba35
last_seen:
  plan_version: "1.2.1"   # v1.3 is pending in PR #6 (read: D-025..D-029, msg 20261108-1501)
  decisions: D-024
  logs: {A: 12, B: 26, C: 20, D: 10}
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
  - 20261108-1510-from-C-sync-and-order.md
blocked_on: none (D-027: the human recorded the pack, so the to-human 1418 key request clears once PR #6 merges)
notes: >
  B-026: C asked (1510) for the asked pair to come first. route() now orders facts with named pairs first,
  then covering flags, then the other subject keys. Order only; sends unchanged. Reply sent to C. Read A-012
  (VLM in capture) and C-020 (sync button, confirm tap); neither affects B. make test exit 0, 627 passed, 1 skipped.
  The untracked Finder copies ("core/cloud 2.py" etc.) are still local only. A human can delete them.
next: G2 merge of PR #2. Once PR #6 merges, rebase on v1.3 and add a sync_pack test against the committed mocks/cloud_cache/ (v5 frozen)
