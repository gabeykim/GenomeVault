agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: merged A+B+C+D verification done; PR #2 rebased on main 4fcd641 and ready for G2
branch: agent/B-privacy-router
last_commit: 2d77102
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 6, B: 16, C: 14, D: 8}
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
blocked_on: ANTHROPIC_API_KEY for the demo cache recording (human, D-019); escalated to to-human; cache must be v5
notes: >
  Verification cycle, no code change. B 2d77102 + A f9db84a + C 3feb861 + D 928224d merged cleanly (octopus,
  no conflicts) in a throwaway worktree: make test exit 0, 723 passed. In that merge, B's v5 tests (one bucket
  per generalized topic, every rules.all_keys() key resolves) and D's test_d_wording pass against A's real rules.
  I did not run `python -m eval.redteam` / `eval.wording` directly (sandbox needs approval); D should confirm the
  splits = {} and 25/25 numbers. router._profile already prefers A's core.graph.load_profile, so nothing to switch
  after G1. C's names (status, set_offline, start_cover, stop_cover, cover_running) are kept.
  Housekeeping: untracked " 2"/" 3" copies of B files keep reappearing in gv-B (same bytes as tracked files, looks
  like Desktop/iCloud sync); left alone, never committed; told the integrator.
next: after G2 merge, freeze v5; take A's no_data helper (A queue 8) in router when it lands; stretch: pack sync polish
