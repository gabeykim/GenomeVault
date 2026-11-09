# For Dhiaa (demo machine): main is final — pull, restart, re-run the beats (flags OFF)

- **From:** integrator (Gabe) · **To:** Dhiaa · **Time:** 2026-11-08 18:00
- **Re:** demo-v1 prep (this is the "go" after the earlier hold)

Main is final for **demo-v1** at **`e7cf0a0`**: the five post-freeze PRs (#22, #20, #18, #21, #23) are merged; CI green, `make test` 1311, `DEMO=1 make eval && python -m eval.gate` = 22/0/0; results regenerated (tail-v2 numbers). `coord/FREEZE` is in place (agent loops stopped). **#19 (GV_INTENT/GV_DIRECT) is held — NOT in this build.**

On the demo machine:
1. `git pull` on `main`.
2. Restart the demo app and Ollama.
3. Re-run the **S1–S7 demo beats with all feature flags OFF** — do **not** set `GV_FUZZY`, `GV_TAIL`, `GV_DEMO_LIVE_FALLBACK`, `GV_INTENT`, or `GV_DIRECT`.
4. Confirm the beats pass with the live vision + local models.

**Ping Gabe when the beats pass** — he'll tag the commit `demo-v1` and the demo runs on that tag.
