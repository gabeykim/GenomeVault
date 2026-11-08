agent: A
state: working     # working | blocked | waiting-review | done | not-started
current_task: queue 8 (no_data marker for unlisted pairs) next; PR #1 ready (queue 1-6)
branch: agent/A-data-rules
last_commit: f9db84a
pr: "#1 (ready) agent/A-data-rules -> main: queue 1-6 (data, normalize, rules X1-X5, D-021, ingest + graph, capture)"
last_seen:
  plan_version: "1.2"
  decisions: D-021
  logs: {A: 6, B: 14, C: 12, D: 8}
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
blocked_on: none
notes: >
  A-006: core/capture.py from_image (D-020): embedded label text (PNG gv:label chunk / JPEG
  comment) or a local tesseract if installed -> normalize; [] if unreadable, never raises;
  from_text typed fallback; demo_png() for sample photos; GV_OCR picks the source. Stdlib only, no
  network. Read C-012 (uses expected_notes; keep the {id,key,text,source} shape) and D-008 (no
  action for A). Messages sent to C and the integrator (optional tesseract on the demo laptop).
next: queue 8 (rules no_data marker for unlisted pairs, for the router), then close queue 7 (X5 done in A-003)
