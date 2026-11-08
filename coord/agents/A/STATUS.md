agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-014 normalize combination strengths ("10-40 mg" in ingredient order; X3 false negative fixed), done, on PR #5
branch: agent/A-data-rules
last_commit: fa0584b
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings + A-014 combo strengths. Rebased on origin/main, make test green (297 passed, 1 skipped)."
last_seen:
  plan_version: "1.2.1"       # v1.3 is in PR #6 (D-025..D-029), not on main yet
  decisions: D-024
  logs: {A: 14, B: 26, C: 20, D: 10}
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
blocked_on: "encryption-at-rest stretch: waiting on the human to decide on the `cryptography` dependency (to-human 1454)"
open_questions:
  - "To human: add `cryptography` for encryption at rest, or drop the stretch? (to-human 1454)"
  - "To I: A-012 codes against PR #6's `local_llm.generate(images=, format=, model=)` and `VLM_MODEL`. Please tell A if that changes before merge."
notes: >
  A-014: "ezetimibe-simvastatin 10-40 mg" read as simvastatin 10 mg, which hid X3. Names joined by - or /
  are now one product, and their strengths go to the ingredients in order. A range or a count that doesn't
  line up gives dose None, which rules treat as "worth asking". drug_names v4 adds amox-clav. Answered C's
  Amoxil question: that label text gives amoxicillin 500 → AL-001 only. Stage time is D/I's call. Message
  to D: optional X3 combo eval case.
next: >
  Live VLM test against qwen2.5vl:7b after PR #6 merges (may need the human, since Ollama can't be reached
  from the headless loop). Otherwise: PR #5 review at G2 (all A queue items done), requests from B/C/D.
