agent: B
state: working            # working | blocked | waiting-review | done | not-started
current_task: bucket partition v2 (frequency-balanced, 112 keys) done, PR #2 updated; queue items 1-9 + stretch done
branch: agent/B-privacy-router
last_commit: f545cff
last_seen:
  plan_version: "1.1"
  decisions: D-013
  logs: {A: 2, B: 11, C: 8, D: 5}
handled_messages:
  - 20261108-1310-from-C-ledger-usage.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1331-from-C-check-output-scope.md
  - 20261108-1323-from-D-eval-needs.md
  - 20261108-1352-from-A-x5-keys.md
  - 20261108-1355-from-C-using-extras.md
  - 20261108-1357-from-D-bucket-numbers.md
blocked_on: none
notes: >
  B-011: data/buckets/v2.json is the default (CURRENT_VERSION="v2"). It has 14 buckets and 112 keys,
  and the worst-bucket statistical attacker drops from 31% (v1) to 22.9% with D's synthetic priors.
  v1 is frozen and still loads. It adds the keys for D's Q05/Q12/Q14/Q20. I asked A to confirm the
  lab-band spellings and D to rerun E1 and add priors for 4 keys. C was told the bucket ids now point
  at different members. Names C relies on (ledger.outbound, kb.stats, generalize.generalize,
  cloud.status, cloud.set_offline) stay stable. mocks/cloud_cache/ is still empty (integrator-owned).
  C's cloud.status() proposal is still unruled.
next: match A's spellings in v2 if they differ (before G2 freezes v2); switch to real A code after G1; G2 merge fixes
