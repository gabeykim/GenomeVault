agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-017 shared label set (C-022, to-A 1526): from_image pinned against phone/samples texts + PNGs, done, on PR #5
branch: agent/A-data-rules
last_commit: 1fd3909
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths + A-015 G3 label test + A-016 eval-query/handoff tests + A-017 shared label set tests. Rebased on origin/main (v1.3), make test green (403 passed, 21 skipped)."
last_seen:
  plan_version: "1.3"
  decisions: D-031
  logs: {A: 17, B: 31, C: 22, D: 11}
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
  - 20261108-1526-from-C-label-set.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
open_questions:
  - "To B/D (FYI, to-integrator 1529): offline + cold KB, B's real router gives no_data for 10 of D's offline_state=known questions (Q01, Q06, Q08, Q12, Q18, Q19, Q20, and Q15/Q17 if caller passes only check_all). Not an A change."
  - "To human: live VLM check on real photos needs Ollama + qwen2.5vl:7b running on this machine (to-human 1523). Optional."
notes: >
  A-017: tests/A/test_capture_shared_samples.py. C's 7 label texts run everywhere; the real phone/samples
  PNGs (C-owned) run once C's PR is on main (15 skips until then) and passed 23/23 against C's branch files.
  Ibuprofen flags X5 x4 for Alex (one per med pair).
next: >
  PR #5 review at G2. Live VLM run on C's PNGs (iTXt stripped) if the human starts Ollama. Otherwise requests from B/C/D.
