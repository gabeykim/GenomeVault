# Agent D — eval-redteam

**Mission:** prove the claims and tell the story (E1–E4, P8 assets, M11).
**Owns:** `eval/`, `docs/`, `slides/`, `tests/D/`
**Provides to others:** test questions, attack results, charts, pitch materials.
**Depends on:** mocks first; integrated build at G4.

## Queue

1. `eval/queries.json`: 20 questions (5 gene–drug, 5 drug–drug, 4 drug–lab, 3 OTC, 3 open-ended). Write before B's router lands.
2. `eval/llm_client.py` + `eval/redteam.py`: three conditions on mocks; JSON results + chart.
3. Joint-inference attacker and statistical attacker with documented synthetic frequency priors.
4. `learning_curve.py`, `latency_cost.py`, `offline.py`.
5. `make eval` regenerates everything on the integrated build. **Gate G4.**
6. `slides/`: pitch outline, demo script (S1–S7), judge Q&A.
7. `docs/`: setup and results write-up.
