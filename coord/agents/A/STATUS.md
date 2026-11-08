agent: A
state: waiting-review     # working | blocked | waiting-review | done | not-started
current_task: queue 5 (ingest + graph) next; PR #1 ready for G1 merge
branch: agent/A-data-rules
last_commit: 6e484af
pr: "#1 (ready) agent/A-data-rules -> main: queue 1 data, 2 normalize, 3 rule tables, 4 rules.check"
last_seen:
  plan_version: "1.1"
  decisions: D-013
  logs: {A: 3, B: 9, C: 7, D: 4}
handled_messages:
  - 20261108-1310-from-C-typed-input.md
  - 20261108-1323-from-C-boundaries.md
  - 20261108-1324-from-B-bucket-keys.md
blocked_on: none
notes: >
  A-003: rule tables + rules.check done. Alex's discharge meds give exactly mocks/flags.json (X1-X4).
  Ibuprofen gives X5 as four flags sharing id X5. Asked C to dedupe by flag.key instead of flag.id.
  clopidogrel|pantoprazole is absent everywhere (S6). G1 deliverable is on PR #1 and waits on the
  integrator merge. graph.load_profile is still the mock (identical data) until queue 5.
next: queue 5 (ingest.py VCF -> phenotypes, graph.py load_profile + stale labs), then 6 (capture), 7 (X5 check), 8 (no_data marker)
