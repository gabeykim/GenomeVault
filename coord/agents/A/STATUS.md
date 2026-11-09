agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-024 standalone `python -m eval.gate` on integrated heads (#4 4bd66e2, #5 f483847, #7 91a39b7, #8 ff5a93c) over main f51ae85. Clean octopus merge; make test 1158 passed, 0 skipped; eval.gate 22 pass, 0 warn, 0 fail (on #4's committed results; sandbox refused DEMO=1 make eval).
branch: agent/A-data-rules
last_commit: f483847
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths + A-015 G3 label test + A-016 eval-query/handoff tests + A-017 shared label set tests + A-018 app real-path tests. Rebased on origin/main 48c182d, make test green (1078 passed, 2 skipped). Merges cleanly with #4 4bd66e2, #7 91a39b7, #8 ff5a93c over main f51ae85 (1158 passed, 0 skipped integrated; python -m eval.gate 22/0/0)."
last_seen:
  plan_version: "1.3.2"
  decisions: D-035
  logs: {A: 24, B: 40, C: 24, D: 13}
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
  - 20261108-1551-from-D-offline-reading.md
  - 20261108-1600-from-D-a016-settled.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Rejected (D-030, to-A 1516, 1522): no `cryptography` dependency, no graph.py change."
open_questions:
  - "To human: a live VLM check on real photos needs Ollama + qwen2.5vl:7b running on this machine (to-human 1523). Optional."
notes: >
  A-024: no code change, PR #5 not re-pushed (main gained only coord commits). On a local temp branch in A's code
  worktree (deleted, nothing pushed) merged main f51ae85 + #4/#5/#7 91a39b7/#8: make test 1158/0 skipped;
  python -m eval.gate run standalone: 22/0/0. DEMO=1 make eval was refused by the sandbox, so the gate read #4's
  committed eval/results.
next: >
  PR #5 review/merge at G3 (17:30); then re-run A's suite on main. Live VLM run on C's PNGs if the human starts Ollama.
  After that, requests from B, C and D.
