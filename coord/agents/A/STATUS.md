agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: A-011 allergy engine (done, on PR #5); core queue 1-8 + PharmCAT stretch complete
branch: agent/A-data-rules
last_commit: 143fa41
pr: "#5 (open) agent/A-data-rules -> main: queue 8 key_state/no_data_keys + A-008 universe names + A-009 PharmCAT path + A-010 genotype sweep + A-011 allergy engine. Rebased on origin/main 01f4f28, make test green (237 passed, 1 skipped). #1 merged at G1 (D-022)."
last_seen:
  plan_version: "1.2.1"
  decisions: D-024
  logs: {A: 11, B: 20, C: 18, D: 9}
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
blocked_on: "encryption-at-rest stretch: waiting on the human to decide on the `cryptography` dependency (to-human 1454)"
open_questions:
  - "To D: should the EX-001 DAPT note make aspirin|clopidogrel `known` offline (A now) or `no_data` (Q08)? B-018's router fix may make this moot; D to confirm on re-run."
  - "To human: add `cryptography` for encryption at rest, or drop the stretch? (to-human 1454)"
notes: >
  A-011: F3 lists allergy as a Must, but no engine produced `engine="allergy"` flags, so Alex's
  penicillin allergy was never checked. New `data/rules/allergy.json` (penicillin and
  sulfonamide-antibiotic groups, listed members only, no cross-group inference, I4) and
  `rules._allergy`. Keys are `allergy:<group>|<ingredient>`. drug_names v3 adds the members' brands.
  Alex's X1-X5 are unchanged. Messages to B (real key shape vs their fixtures), C (flags now reach
  actions/UI) and D (eval question idea). Read C-017/C-018 (palette only; sample labels still read
  with capture.from_image), so no A change. No new inbox, DECISIONS or PLAN version.
next: >
  PR #5 review at G2. Encryption at rest only if the human approves the dependency. Otherwise:
  requests from B/C/D.
