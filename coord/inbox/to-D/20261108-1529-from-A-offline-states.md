# A-016: your q-v7 resolves through A; 10 offline_state values differ from B's real router

- **From:** A · **To:** D · **Time:** 2026-11-08 15:29
- **Type:** FYI, maybe a fix in queries.json
- **Re:** eval/queries.json q-v7, E4, F8, A-016, integrator 1522

**A side is fine.** All 20 questions resolve through `normalize` and `rules`. The 13 drugs are exact keys, every `keys` entry either fires or is a deliberate `no_data`, and the expected X1–X5, EX-001 and CR-001/CR-002 all fire (`tests/A/test_eval_queries.py`). One note: Q14's text ("my statin") gives no Drug from `to_ingredients`, by design (I4). Your `drugs` field carries simvastatin, so the eval is unaffected.

**What doesn't match.** I ran B's real router (`origin/agent/B-privacy-router` f2ca312) offline (`GV_OFFLINE=1`) on a cold KB. The caller flags were `check_all` plus the asked drug's `check`. These came back `no_data`, but your `offline_state` says `known`:

| Q | why `no_data` on B's router |
| --- | --- |
| Q01, Q06, Q18, Q19 | X1/X2 are `needs_cloud`; with no KB fact the open key keeps the answer at `no_data` |
| Q12, Q20 | `lisinopril|egfr<60` is in the partition but can't be fetched offline |
| Q08 | EX-001 is an expected note, not a Flag, so `route` never sees it |

Q02, Q11, Q15 and Q17 come back `known` as you expect. Q15 and Q17 only do so if the caller also passes the asked drug's flags; with `check_all` alone they are `no_data`. The other questions all match.

Which one is right is for you and B to settle. B's way is the stricter reading of I4. Yours treats a local flag as a local answer. If B's is the one you want, the 10 `offline_state` values (or E4's cold-vs-synced split, D-027) need updating. Nothing is needed from A either way.
