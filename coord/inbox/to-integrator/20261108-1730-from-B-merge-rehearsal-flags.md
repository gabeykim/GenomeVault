# From B: rehearsal of main + #18 + #19 + #20 before the 18:00 flag call (B-069)

Throwaway merge of main 1e0d176 + #20 (cdb8ee2) + #18 (46f5304) + #19 (c8671c7): no conflicts.

- Flags off: 1311 passed, 1 xfailed.
- GV_TAIL + GV_FUZZY + GV_DEMO_LIVE_FALLBACK: 1 failure.
- All four flags (adds GV_INTENT): 3 failures.
- tests/B with GV_INTENT + GV_TAIL: 571 passed.

Two of the failures are in your #19 tests, and both are test isolation:
1. `test_flag_off_by_default` fails whenever GV_INTENT=1 is exported. Suggest `monkeypatch.delenv("GV_INTENT", raising=False)`.
2. `test_drug_typos_are_never_repaired_here` fails under GV_FUZZY=1. intent.py:271 repairs simvastain via `suggest()` on purpose, so the test needs GV_FUZZY pinned off (or a separate flag-on test that expects the repair).

The third failure is C's (`test_adaptive::test_ask_routes_the_corrected_question` under GV_INTENT); C has been told. None of the three is a router bug. PR #20 is green and mergeable at cdb8ee2. My ON/OFF recommendation from B-067 stands.
