# Integrator pass: cloud.status + cloud_cache recording (D-019, D-020)

- **From:** integrator (Gabe, backup) · **To:** B · **Time:** 2026-11-08 14:04
- **Type:** ruling + task
- **Re:** D-020, D-019, CONTRACTS, M8, I2, S6

**New contract (D-020):** implement `cloud.status() -> dict` with keys `online: bool` and `demo: bool` (M8, queue 9). It must **send nothing** (I2) — report the state you already know. A mock stub lives in `core/interfaces.py` until G3.

**cloud_cache (D-019):** recording `mocks/cloud_cache/*.json` needs a real `ANTHROPIC_API_KEY`, which is **not** in the integrator's environment. Please either:
- (a) run `ANTHROPIC_API_KEY=... python -m core.cloud record mocks/cloud_cache` and send me the JSON, or
- (b) tell me and I'll record it once a key is available.

It must land before **G2 (16:00)**. No key will be committed. If A's real X5 keys later change the buckets (v2), note that the cache has to be re-recorded.
