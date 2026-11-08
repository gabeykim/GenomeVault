agent: B
state: working            # working | blocked | waiting-review | done | not-started
current_task: bucket partition v3 (covers every key in A's rules.all_keys(), 136 keys / 17 buckets) done, PR #2 updated; queue items 1-9 + stretch done
branch: agent/B-privacy-router
last_commit: a951d58
last_seen:
  plan_version: "1.1"
  decisions: D-013
  logs: {A: 3, B: 12, C: 9, D: 5}
handled_messages:
  - 20261108-1310-from-C-ledger-usage.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1331-from-C-check-output-scope.md
  - 20261108-1323-from-D-eval-needs.md
  - 20261108-1352-from-A-x5-keys.md
  - 20261108-1355-from-C-using-extras.md
  - 20261108-1357-from-D-bucket-numbers.md
  - 20261108-1359-from-A-rules-ready.md
blocked_on: none
notes: >
  B-012: data/buckets/v3.json is the default (CURRENT_VERSION="v3"). It is v2's 112 keys + the 15 keys
  A's rule tables can emit that v2 lacked (incl. needs_cloud CYP2C19:intermediate_metabolizer|clopidogrel
  and D's Q17 naproxen keys) + 9 decoys. Worst-bucket statistical attacker is 22.2% (v2: 22.9%). v1/v2 stay frozen.
  A guard test checks rules.all_keys() against the universe once core/rules.py is on main. I asked D to
  rerun E1 and add priors for 15 new pair topics; told C the ids are now b01-b17. C's cloud.status()
  proposal is still unruled. C-009 (tabs UI) needs nothing from B. mocks/cloud_cache/ still empty (integrator-owned).
next: rebuild v3 if D sends priors before G2 (frozen from G2); switch to real A code after G1 (graph.load_profile); G2 merge fixes
