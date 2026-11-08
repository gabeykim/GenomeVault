agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-012 VLM label reader in capture.from_image (D-029), done, on PR #5
branch: agent/A-data-rules
last_commit: 271985d
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine + A-012 VLM capture. Rebased on origin/main, make test green (267 passed, 1 skipped). B trial-merged #5 with #2: green (B-023)."
last_seen:
  plan_version: "1.2.1"       # v1.3 is in PR #6 (D-025..D-029), not on main yet
  decisions: D-024
  logs: {A: 12, B: 23, C: 19, D: 10}
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
  - "To I: A-012 codes against PR #6's `local_llm.generate(images=, format=, model=)` and `VLM_MODEL`. Please tell A if that changes before merge."
notes: >
  A-012: read the integrator's PLAN v1.3 heads-up on PR #6 (D-029: label photos via the local VLM
  behind A's capture.from_image). Added a VLM source between embedded text and tesseract. The VLM only
  reads; names still go through the exact-key table (I4), and conflicts give []. It is a no-op until
  PR #6 merges and LOCAL_VLM_MODEL is set, so #5 merges green in either order. Q08 closed by D (keep
  key_state). B confirmed the allergy keys and asked to keep the `allergy:` prefix. Messages to C
  (no change needed, maybe add a spinner) and D (optional eval case).
next: >
  After PR #6 merges: test the VLM path against a live qwen2.5vl:7b with synthetic label photos for
  S2. Re-read PLAN v1.3 gates (G3 17:30). Otherwise: PR #5 review at G2, requests from B/C/D.
