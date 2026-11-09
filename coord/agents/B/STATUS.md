agent: B
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: B-070 re-test after coord-only moves on main (6ed0e77); PR #20 held at cdb8ee2 (green) pending Gabe
branch: agent/B-privacy-router
last_commit: cdb8ee2
last_seen:
  plan_version: "1.3.6"
  decisions: D-042
  logs: {A: 35, B: 70, C: 30, D: 18}
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
  - 20261108-1638-from-integrator-g4-passed.md
  - 20261108-1644-from-integrator-codespaces-cover-interval.md
  - 20261108-1645-from-human-uncovered-pair-reads-checked.md
  - 20261108-1658-from-integrator-adaptive-questions-pending.md
  - 20261108-1702-from-I-adaptive-parts2-3.md
  - 20261108-1702-from-C-single-and-tail-shape.md
  - 20261108-1708-from-C-d040-ui-ready.md
  - 20261108-1709-from-integrator-d041-single-tail-contract.md
  - 20261108-1717-from-D-tail-finding.md
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
  B-049: PR #10 rebased onto main 42a520b (coord-only changes), head abc231a, make test exit 0, 1160 passed.
  B-050: PR #10 rebased onto main 7d8e02a (coord-only changes), head 86cb882, make test exit 0, 1160 passed.
  B-051: PR #10 rebased onto main 4960c3b (coord-only changes), head a68211a, make test exit 0, 1160 passed.
  B-052: main moved only by the B-051 report (3a59953). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (green, mergeable), no re-push.
  B-053: main moved only by coord reports (ba0b144, 20606ab, 8d3c339). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (2/2 checks green), no re-push.
  B-054: main moved only by coord reports (ae8b2fd, 7766f85). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (2/2 checks green), no re-push.
  B-055: main moved only by coord reports (61e7c0a, f18a179). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (2/2 checks green), no re-push.
  B-056: main moved only by coord reports (c095b5a, a1e2851). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (2/2 checks green), no re-push.
  B-057: main moved only by coord reports (eca9e08, d88ebdc). Re-tested locally (exit 0, 1160 passed); PR #10 left at a68211a (2/2 checks green), no re-push.
  B-058: G4 passed (D-038, PLAN v1.3.4). Owner report fixed (I4): a named pair with no fact and no flag on that exact pair
  ("pantoprazole with my lisinopril") now answers no_data / OFFLINE_TEXT instead of LOCAL_TEXT "checked on your device".
  Substitution questions ("instead of") unchanged. Commit ccf2c4f on PR #10, make test exit 0, 1163 passed, eval gate 22/0/0.
  C needs no merge change (high flags still listed under no_data).
  B-059: PR #10 merged (c59a2c5) with #9, #11, #12. Branch = main 41f5912, make test exit 0, 1177 passed. No open B PR.
  D-039 Codespaces sets GV_COVER_INTERVAL_S=20 (existing B setting, valid). Nothing for B to change.
  B-060: PR #15 (tests only, c4c4998) pins D-039 GV_COVER_INTERVAL_S=20: waits 10-30 s jittered, one bucket per tick.
  make test exit 0, 1178 passed. Integrator told (no objection to 20 s).
  B-061: main moved only by coord reports (b05ad09, 6895a77, c7f159f). Re-tested locally (exit 0, 1178 passed); PR #15 left at c4c4998 (2/2 checks green), no re-push.
  B-062: main moved only by coord commits (2854856, 95a71d1, 4603f3e). Re-tested locally (exit 0, 1178 passed); PR #15 left at c4c4998 (2/2 checks green), no re-push.
  New proposal 20261108-1655-human-adaptive-questions (I4, I5) not yet ruled: nothing started. Integrator told B's plan (part 3 then part 2, flags default OFF).
  B-063: main moved only by coord commits (87d3ba8, 31ab9e3). Re-tested locally (exit 0, 1178 passed); PR #15 left at c4c4998 (open, mergeable), no re-push. Proposal still unruled.
  B-064: D-040 accepted (PLAN v1.3.5). Part 3 GV_DEMO_LIVE_FALLBACK in core/cloud.py (0705cbe, PR #15): DEMO=1 + flag + key,
  a cache miss asks the whole bucket live (I5) with live delays; cached answers kept; live failure = replay only; forced offline wins.
  Flag default off. make test exit 0, 1186 passed. C and D told the API.
  B-065: D-040 part 2 GV_TAIL (3403f65, PR #15): data/buckets/tail-v1.json (1047 buckets, 8376 keys, built by
  build_tail_v1.py, seed 20261108) = every drug-drug pair over A's vocabulary + one drug-lab key per ingredient/lab,
  minus v5. Router: core first, then the tail bucket through every P6 step (ledger bucket_id tail-NNNN). Other bands
  alias onto the one tail drug-lab key (I3). Cover: fair coin core/tail. single_candidates/send_single as C proposed
  (ledger bucket_id "single", refused for partition keys). Flag default off. make test exit 0, 1200 passed.
  Not run: full suite with GV_TAIL=1 exported (sandbox refused). C and D told.
  B-066: full suite with GV_TAIL, GV_DEMO_LIVE_FALLBACK, GV_FUZZY on (set inside Python) on a throwaway merge main + #15 + #16 + #17
  found 3 router bugs: a covering local flag was overridden by a tail send (wrong no_data). Fixed (97f83f3): same-product
  ingredients never a pair; tail drug-lab keys only when no flag covers; substitution asks no tail-only pair. make test exit 0,
  1207 passed; merge flags off 1263 passed, flags on 1263 passed. C's single shapes confirmed. C, D, integrator told.
  B-067: tests/B/test_d041_contract.py pins router.single_candidates/send_single to the D-041 interfaces stubs
  (same params and type hints; flag off = stub output, no ledger row). make test exit 0, 1216 passed. Merge main + #15 + #16 + #17:
  flags off 1282, flags on 1282, eval with flags on G4 22/0/0 (no tail pair in eval, live fallback not run without a key).
  Recommendation to integrator: GV_TAIL + GV_DEMO_LIVE_FALLBACK ON only with a working key on the demo machine, else OFF.
  B-068: PR #15 merged. D's E1 finding (tail-v1 statistical attacker 59%): new data/buckets/tail-v2.json (build_tail_v2.py,
  same 8376 keys, tiered by unseen count then product of synthetic priors), TAIL_VERSION = tail-v2. Stat attacker 0.15
  (ceiling 0.129), 0.13 with unseen at median; repeat-ask ~0.11. make test exit 0, 1293 passed. PR #20. D asked to point
  eval/adaptive.py TAIL_FILE at tail-v2.json.
  B-069: PR #20 rebased onto main 1e0d176 (head cdb8ee2, 2/2 green), make test exit 0, 1293 passed. Merge main + #18 + #19 + #20:
  flags off 1311 passed + 1 xfail; all flags on 3 failures, all test isolation in I's #19 (2) and C's test_adaptive (1), none in B.
  I and C told.
  B-070: main moved only by coord commits (0f06609 escalated B's all-OFF flag rec + PR #20 to Gabe). Re-tested locally
  (exit 0, 1293 passed); PR #20 left at cdb8ee2 (2/2 green), no re-push.
next: if GV_TAIL goes ON, #20 merges first, then re-run flags-on suite + eval on main; else hold for G5 freeze.
