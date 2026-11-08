agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-016 G2 support (D-030): D's 20 eval questions resolve through normalize/rules + rules.check_all → router.route handoff test, done, on PR #5
branch: agent/A-data-rules
last_commit: 25cd41d
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths + A-015 G3 label test + A-016 eval-query/handoff tests. Rebased on origin/main (v1.3), make test green (395 passed, 6 skipped)."
last_seen:
  plan_version: "1.3"
  decisions: D-031
  logs: {A: 16, B: 29, C: 21, D: 11}
handled_messages:
  - 20261108-1310-from-C-typed-input.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1324-from-B-bucket-keys.md
  - 20261108-1404-from-integrator-pgx-and-capture.md
  - 20261108-1405-from-D-dedupe-ack.md
  - 20261108-1408-from-B-rule-keys-covered.md
  - 20261108-1410-from-B-v2-lab-bands.md
  - 20261108-1414-from-C-x5-fixed.md
  - 20261108-1426-from-D-re-ingest.md
  - 20261108-1441-from-C-capture-wired.md
  - 20261108-1500-from-D-q08-note-counts.md
  - 20261108-1501-from-I-plan-v1-3.md
  - 20261108-1502-from-B-allergy-keys-ok.md
  - 20261108-1510-from-C-allergy-nodata.md
  - 20261108-1516-from-human-skip-encryption.md
  - 20261108-1518-from-D-optional-cases.md
  - 20261108-1522-from-integrator-g2-support.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
open_questions:
  - "To B/D (FYI, to-integrator 1529): offline + cold KB, B's real router gives no_data for 10 of D's offline_state=known questions (Q01, Q06, Q08, Q12, Q18, Q19, Q20, and Q15/Q17 if caller passes only check_all). Not an A change."
  - "To human: live VLM check on real photos needs Ollama + qwen2.5vl:7b running on this machine (to-human 1523). Optional."
notes: >
  A-016: tests/A/test_eval_queries.py. All 13 drugs in D's q-v7 are exact normalize keys; every listed
  key is curated-and-fires or a deliberate no_data (pairs marked by no_data_keys). check_all → route is
  pinned on contract types; real-router parts (offline, 0 bytes, X3/X4/X5 local known, X1/X2 bucketable)
  skip on main until G2 and passed against B's f2ca312 in a scratch worktree (46 passed).
next: >
  PR #5 review at G2. Live VLM run on real photos if the human starts Ollama. Otherwise requests from B/C/D.
