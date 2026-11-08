# cloud.py is on PR #2; mocks/cloud_cache/ needs content for demo mode

- **From:** B · **To:** I · **Time:** 2026-11-08 13:50
- **Type:** request
- **Re:** M8, I8, S4, B-005, commit 54b170c

`core/cloud.py` replays `mocks/cloud_cache/*.json` when `DEMO=1`. The format is a JSON object `{exact key: answer text}`, in any number of files. That directory is yours and empty right now, so in demo mode every cloud question comes back `no_data`.

To fill it (needs a real key in the environment, never committed):

    ANTHROPIC_API_KEY=... python -m core.cloud record mocks/cloud_cache

This writes `b01.json`..`b12.json` (96 answers from the v1 partition). Please commit them on main before G2 (16:00), or tell me if you'd rather I generate the JSON and send it to you. If A's real X5 keys change the buckets later (v2), the cache has to be recorded again.
