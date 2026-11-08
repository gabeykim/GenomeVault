agent: B
state: working            # working | blocked | waiting-review | done | not-started
current_task: I7 wording filter hardened against D's red team (B-016), PR #2 updated
branch: agent/B-privacy-router
last_commit: 85ab929
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 5, B: 16, C: 12, D: 8}
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
blocked_on: ANTHROPIC_API_KEY for the demo cache recording (human, D-019); escalated to to-human; cache must be v5
notes: >
  B-016: wording_problems now normalizes text (NFKC, zero-width, look-alikes, spelled-out letters) and
  rejects reassurance synonyms, non-English, and advice in any form. D's red team: 25/25 caught, 0 false
  alarms (was 3/25, 1). Classed Refines (stricter I7, no contract change). Kept sequential live delays
  (P6.4 timing cover) despite D's 8x latency note. A-005 phenotype names match v5 keys; nothing to do.
next: merged run with A/C/D branches (D's splits empty on v5, eval.wording 25/25); switch to real A code after G1; freeze v5 from G2
