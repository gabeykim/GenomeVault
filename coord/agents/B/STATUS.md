agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-020 tests/B ignores untracked Finder duplicate test files; PR #2 updated (425f764), CI green, ready for G2
branch: agent/B-privacy-router
last_commit: 425f764
last_seen:
  plan_version: "1.2.1"
  decisions: D-024
  logs: {A: 8, B: 20, C: 16, D: 9}
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
blocked_on: ANTHROPIC_API_KEY for the demo cache recording (human, D-019; to-human 1418; cache must be v5)
notes: >
  Rebased on main (only coord commits since B-019, no conflicts). No new inbox, DECISIONS or LOG entries.
  tests/B/conftest.py now skips the untracked Finder copies ("test_* 2.py" etc.), which had added 439
  duplicate tests locally; make test exit 0, 619 passed (matches CI). The copies themselves are left on disk
  untouched. Queue 1–9 done; PR #2 CI green and waiting on the G2 merge. No messages needed (affects nobody).
next: G2 merge of PR #2, then freeze v5; record the demo cache once the key is available; otherwise stretch (knowledge-pack sync)
