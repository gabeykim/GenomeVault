agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-018 I4 fix in router.route (no_data unless a covering flag or a fact backs it); PR #2 updated (cafebe3), ready for G2
branch: agent/B-privacy-router
last_commit: cafebe3
last_seen:
  plan_version: "1.2.1"
  decisions: D-022
  logs: {A: 7, B: 18, C: 15, D: 9}
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
blocked_on: ANTHROPIC_API_KEY for the demo cache recording (human, D-019; to-human 1418; cache must be v5)
notes: >
  D's I4 report fixed: route() reads the question's subject locally (named pairs, gene-drug keys on "genes",
  drug-lab keys on a lab word) and is `known` only with facts or a covering flag and nothing answerable left
  open. Merge of B+D+C+A: eval.gate I4 PASS, offline 20/20, all 20 online expected states match under DEMO
  replay. make test exit 0 (1055). A's no_data helper (A-007) is noted; the router does not need it now.
  Told D (to-D 1445, also an I7a import oddity in eval/wording.py) and C (to-C 1445, FYI).
next: G2 merge of PR #2, then freeze v5; record the demo cache once the key is available; stretch: pack sync polish
