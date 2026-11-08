agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-013 capture.label_drugs (one label = one product, warning names dropped), done, on PR #5
branch: agent/A-data-rules
last_commit: 9e94292
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture + A-013 label warnings. Rebased on origin/main, make test green (279 passed, 1 skipped)."
last_seen:
  plan_version: "1.2.1"       # v1.3 is in PR #6 (D-025..D-029), not on main yet; read it there
  decisions: D-024
  logs: {A: 13, B: 24, C: 19, D: 10}
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
blocked_on: "encryption-at-rest stretch: waiting on the human to decide on the `cryptography` dependency (to-human 1454)"
open_questions:
  - "To human: add `cryptography` for encryption at rest, or drop the stretch? (to-human 1454)"
  - "To I: A-012 codes against PR #6's `local_llm.generate(images=, format=, model=)` and `VLM_MODEL`. Checked again at 15:12: it matches the PR #6 head. Please tell A if it changes before merge."
notes: >
  A-013: real labels name other drugs in their warnings ("do not take aspirin or ibuprofen"), and
  reading the whole text made one Plavix photo fire X5. label_drugs keeps the first line or sentence
  that names a drug. This applies to embedded and tesseract text; typed text and the VLM are unchanged.
  C's samples are unaffected. Messages to C (FYI, plus an optional phone-side downscale for the VLM) and
  D (optional eval case). PR #6's to-A v1.3 note has been read on its branch (G3 17:30, D-029 matches A-012).
next: >
  Live VLM test against qwen2.5vl:7b after PR #6 merges. The headless loop can't reach Ollama here, so
  this may need the human. Otherwise: PR #5 review at G2 (all A queue items done), requests from B/C/D.
