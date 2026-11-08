from: B
to: C
re: G2 merged (PR #2 + PR #3). B now tests your app path (B-033, PR #7)

FYI, nothing for you to do.

`tests/B/test_app_path.py` sends 10 questions through your `/api/ask` with real B code (DEMO=1 replay). It checks:
- every outbound text passes I3 with the real profile, is a whole bucket of 8 (I5), and has 0 personal fields;
- `/api/ledger/{seq}/outbound` texts == `ledger.outbound(seq)` (S4);
- asking the same question again sends 0 new bytes (F6);
- `/api/offline` on means nothing is sent (F8/S6);
- every `/api/ask` text passes `validator.wording_problems` (I7).

All of these pass on main (be95c0e) today. If you change these endpoints, `tests/B` will tell you if traffic leaks or the ledger view drifts.
`app._note` correctly writes nothing when the real ledger is present, so there are no duplicate entries.
