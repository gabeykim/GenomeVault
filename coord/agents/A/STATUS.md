agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-015 G3 capture test (Alex's 5 discharge labels + Amoxil, every local path) + warning lines never stand in for the product, done, on PR #5
branch: agent/A-data-rules
last_commit: 24c5148
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths + A-015 G3 label test. Rebased on origin/main, make test green (353 passed, 1 skipped)."
last_seen:
  plan_version: "1.2.1"       # v1.3 is in PR #6 (D-025..D-029), not on main yet
  decisions: D-024
  logs: {A: 15, B: 27, C: 21, D: 11}
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
  - 20261108-1502-from-B-allergy-keys-ok.md
  - 20261108-1510-from-C-allergy-nodata.md
  - 20261108-1516-from-human-skip-encryption.md
  - 20261108-1518-from-D-optional-cases.md
blocked_on: none
dropped:
  - "Stretch: encryption at rest. Dropped by the human (to-A 1516): no `cryptography` dependency, no graph.py change."
open_questions:
  - "To I: A-012 codes against PR #6's `local_llm.generate(images=, format=, model=)` and `VLM_MODEL`. Please tell A if that changes before merge."
  - "To human: live VLM check on real photos needs Ollama + qwen2.5vl:7b running on this machine (to-human 1523). Optional."
notes: >
  A-015: G3 check done. Six full synthetic labels (Alex's 5 discharge meds + Amoxil) each give exactly the
  right Drug via PNG, JPEG, faked OCR and a faked VLM, and flag like the typed name (X1–X4, AL-001). Unknown
  and look-alike names give []. Fixed a false-drug path: an unreadable product line let the warning's drug
  ("Avoid omeprazole") stand in. Warning sentences (cue before any drug name) no longer count. C was told;
  no change is needed on C's side.
next: >
  Live VLM run on real label photos once PR #6 merges and the human starts Ollama. Otherwise: PR #5 review
  at G2, requests from B/C/D.
