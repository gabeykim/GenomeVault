# Need: ANTHROPIC_API_KEY to record the demo cache before G2 (16:00)

- **From:** B · **To:** human (Dhiaa / Gabe) · **Time:** 2026-11-08 14:18
- **Re:** AGENTS.md §9 (secret needed), D-019, I8, S4/S6

The demo cache `mocks/cloud_cache/` is empty (0/136), which blocks S4/S6. Recording it needs a real API key, and no agent or integrator environment has one. A human with a key should run this from the B branch or from main after PR #2 merges:

    ANTHROPIC_API_KEY=… python -m core.cloud record mocks/cloud_cache
    python -m core.cloud check     # exit 0 = ready

Then commit `mocks/cloud_cache/*.json` (integrator-owned). Never commit the key.
