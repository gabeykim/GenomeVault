agent: B
state: working            # working | blocked | waiting-review | done | not-started
current_task: bucket partition v4 (CYP2D6 decoys dropped after D-021, I5) done, PR #2 updated; cloud.status (D-020) already done in B-010; queue items 1-9 + stretch done
branch: agent/B-privacy-router
last_commit: 800a75f
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 3, B: 14, C: 10, D: 6}
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
blocked_on: ANTHROPIC_API_KEY for the demo cache recording (human, D-019); escalated to to-human
notes: >
  B-014: v4 is the default partition (17 buckets, 136 keys). D-021 makes CYP2D6 not_assessed for every user,
  so v3's 7 CYP2D6 decoys were known fakes (b04 had effective k 4, which breaks I5). v4 swaps them for
  SNP-callable gene keys. Only b01-b04 change; b05-b17 are identical to v3. The demo cache must be recorded
  against v4. That needs a real API key, which no agent has, so I escalated it to-human (§9). Replied (b) to the
  integrator. cloud.status() returns {online, demo, forced_offline} and sends nothing. I removed stray untracked
  " 2" duplicate files from my code worktree. Main has a stray to-C/"...offline-status 2.md" and I asked the integrator to remove it.
next: switch to real A code after G1 (graph.load_profile, rules); G2 merge fixes; keep v4 frozen from G2
