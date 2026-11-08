agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-019 brand names in the question count as their ingredient (I4); PR #2 updated (6b81173), ready for G2
branch: agent/B-privacy-router
last_commit: 6b81173
last_seen:
  plan_version: "1.2.1"
  decisions: D-024
  logs: {A: 8, B: 19, C: 16, D: 9}
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
  Rebased on main (no conflicts). Found and fixed an I4 gap: the router matched only bare ingredient words,
  so "Plavix with Protonix" named no drug and a local clopidogrel flag answered `known`. _named_drugs now
  also uses A's normalize.to_ingredients (G1 contract), limited to the universe. make test exit 0 (1058).
  Told C (to-C 1449, FYI) and D (to-D 1449, optional eval query). A-008: v5 adds no new drugs, so nothing for A.
  Untracked Finder duplicates ("* 2.py", "* 3.py") sit in my owned paths; they are untracked and not collected.
next: G2 merge of PR #2, then freeze v5; record the demo cache once the key is available
