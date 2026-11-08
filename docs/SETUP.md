# Running the evaluations

Everything here uses synthetic data only (I1) and runs offline by default.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make eval        # regenerates eval/results/*.json, docs/charts/*.svg and docs/results.md
make test        # includes tests/D/
```

| Command | What it measures (PLAN P7) | Output |
| --- | --- | --- |
| `python -m eval.redteam` | E1: naive vs random decoys vs fixed buckets; repeat-ask, statistical and joint-inference attackers | `eval/results/redteam.json`, `docs/charts/redteam.svg`, `docs/charts/joint.svg` |
| `python -m eval.learning_curve` | E2: cloud calls per question over the 20 scripted questions | `learning_curve.json`, `learning_curve.svg` |
| `python -m eval.latency_cost` | E3: local-only vs cloud-only vs hybrid | `latency_cost.json`, `latency_cost.svg` |
| `python -m eval.offline` | E4: cold vs warm knowledge base with no network | `offline.json`, `offline.svg` |

## Inputs

- `eval/queries.json`: the 20 scripted questions (5 gene–drug, 5 drug–drug, 4 drug–lab, 3 OTC, 3 open-ended), each with exact keys, expected flags and states, and a reference answer.
- `eval/fixtures/universe_v1.json`: 64 generalized topic keys with **synthetic** priors, clinical domains and co-prescription clusters.
- Bucket partition: B's `data/buckets/v1.json` when present, else D's stand-in `eval/fixtures/buckets_v1.json` (rebuild with `python -m eval.fixtures.build_buckets`).

## Simulated vs live

Until B's router and ledger merge (G2), E1 uses a simulated wire and E2–E4 a simulated P6 backend (`eval/backends.py`).
Counts follow from the design; latency and tokens are modelled constants. `run_all` switches to the live build
automatically when `core.router`, `core.ledger`, `core.rules` and `core.graph` import, and `docs/results.md` states which one ran.

## Optional LLM attacker

```bash
EVAL_LLM=1 make eval
```

Needs the `anthropic` package (requested from the integrator) and credentials in the environment. Model:
`EVAL_ATTACKER_MODEL`, else `CLOUD_MODEL`, else `claude-opus-5-5`. Responses are cached in `eval/cache/llm/`;
`EVAL_REPLAY=1` replays the cache with no network. `eval/llm_client.py` is the only file in `eval/` that may call a model (I2).
