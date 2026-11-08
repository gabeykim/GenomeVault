# Integrator pass: anthropic added, cloud.status available, eval DAPT note (D-016, D-020, D-021)

- **From:** integrator (Gabe, backup) · **To:** D · **Time:** 2026-11-08 14:04
- **Type:** ruling
- **Re:** D-016, D-020, D-021, P7 E1/E3, E4, I2

- **anthropic (D-016):** added to `requirements.txt`. `eval/llm_client.py` may import it lazily; it runs only when `EVAL_LLM=1` with credentials in the environment (never committed). Deterministic evals, `make eval`, and `make test` keep working without it.
- **cloud.status (D-020):** `cloud.status() -> {online, demo}` is now a contract (owner B); you may use it in `eval/offline.py` (E4). Stub in `core/interfaces.py` until G3.
- **eval scoring (D-021):** do **not** count `aspirin|clopidogrel` as a missed flag — it is expected DAPT shown as an informational note, not a flag. The NSAID + antiplatelet case (ibuprofen, X5) is still a real flag.
