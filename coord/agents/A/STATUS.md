agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-021 full G3 sequence on current heads (#4 5112526, #5 d81a2b0, #7 f3a4abc, #8 ff5a93c). Clean octopus merge; make test 1156 passed, 0 skipped; core.cloud check 136/136; make eval DEMO=1 + eval.gate 20 pass, 0 fail.
branch: agent/A-data-rules
last_commit: d81a2b0
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths + A-015 G3 label test + A-016 eval-query/handoff tests + A-017 shared label set tests + A-018 app real-path tests. Rebased on origin/main v1.3.1 (aa30bbf), make test green (1078 passed, 2 skipped). Merges cleanly with #4, #7, #8 on their current heads (1156 passed, 0 skipped integrated; eval gate 20/20)."
last_seen:
  plan_version: "1.3.1"
  decisions: D-034
  logs: {A: 21, B: 36, C: 24, D: 11}
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
  - 20261108-1535-from-integrator-g2-passed.md
  - 20261108-1537-from-C-label-pngs-recolored.md
  - 20261108-1543-from-C-app-real-path-ack.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
open_questions:
  - "To B/D (FYI, to-integrator 1529): when offline with a cold KB, B's real router gives no_data for 10 of D's offline_state=known questions (Q01, Q06, Q08, Q12, Q18, Q19, Q20, plus Q15/Q17 if the caller passes only check_all). Not an A change."
  - "To human: a live VLM check on real photos needs Ollama + qwen2.5vl:7b running on this machine (to-human 1523). Optional."
  - "To D (to-D 1550): PR #4's committed eval numbers are simulated; on the integrated build cloud calls 6->11 and on-device 75%->50%. slides/pitch.md quotes the old ones. D re-runs make eval after merge."
notes: >
  A-021: no code change. Rebased and force-pushed PR #5 (d81a2b0). Ran the full G3 sequence on a local throwaway octopus
  branch (deleted, nothing pushed from it): make test 1156/0 skipped, core.cloud check 136/136, make eval DEMO=1 (no API
  spend) and eval.gate 20 pass, 0 fail. check_ownership and check_network were not run.
next: >
  PR #5 review/merge at G3 (17:30). Live VLM run on C's PNGs if the human starts Ollama. After that, requests from B, C and D.
