# Dependency request: anthropic SDK (for eval/llm_client.py)

- **From:** D · **To:** integrator · **Time:** 2026-11-08 13:23
- **Type:** request
- **Re:** I2, P7 E1 (LLM attacker), E3 (quality judge), D-002

`eval/llm_client.py` (the only model caller in `eval/`) uses the official `anthropic` Python SDK, imported lazily. Please add `anthropic` to `requirements.txt` when convenient (before G4). Without it the LLM attacker and quality judge are skipped and reported as such; every deterministic eval, `make eval` and `make test` work without it. It also needs credentials in the environment at run time (only when `EVAL_LLM=1`). No key is stored in the repo.
