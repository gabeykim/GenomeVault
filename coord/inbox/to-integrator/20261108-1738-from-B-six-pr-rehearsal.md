# Six-PR merge rehearsal green; one DEMO=0 gap in #19 tests

- **From:** B · **To:** integrator · **Time:** 2026-11-08 17:38
- **Re:** to-human/20261108-1735-from-integrator-needs-gabe-merges-pr18-22.md; D-040, D-041, G5; B-074

Your suggested order, plus #23, merged as a throwaway onto main 2dffacf: #22 b991470, then #18 e34e618, #21 c6e05f4, #20 f4891e2, #23 5398fad, #19 ecbf7c6. **No conflicts.** `make test` exit 0, 1335 passed in all three runs:
- DEMO unset (as CI runs);
- DEMO=1;
- DEMO=1 with GV_TAIL, GV_DEMO_LIVE_FALLBACK, GV_FUZZY, GV_INTENT and GV_DIRECT exported.

The flag-leak fails B saw in B-069 are gone.

**One gap, in integrator-owned tests only (PR #19):** `tests/I/test_direct.py:10` and `tests/I/test_intent.py:10` use `os.environ.setdefault("DEMO", "1")`. A shell that exports `DEMO=0` keeps 0, so the cloud cache is never replayed. Then `test_examples_lead_first[]`, `test_examples_lead_first[1]` and `test_direct_reads_the_rewritten_question` fail on a correct no_data answer. Main + #19 alone shows the same 3 failures. This is not a product bug. Suggested fix: set DEMO=1 per test with `monkeypatch.setenv` or `mock.patch.dict`. Import-time setdefault also leaks DEMO=1 into every test collected after it. The fix is optional if nobody exports DEMO=0.
