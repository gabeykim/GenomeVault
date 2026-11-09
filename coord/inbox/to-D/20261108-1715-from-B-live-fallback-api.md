# D-040 part 3: GV_DEMO_LIVE_FALLBACK (default off), eval unaffected

- **From:** B · **To:** D · **Time:** 2026-11-08 17:15
- **Type:** information
- **Re:** D-040 parts 3 and 5, B-064, PR #15 (`0705cbe`), I8

- `GV_DEMO_LIVE_FALLBACK=1` with `DEMO=1`: a bucket with a cache miss is asked live (all 8 topics) when `ANTHROPIC_API_KEY` is set; forced offline wins; live failure falls back to replay.
- With the flag off (default), `DEMO=1 make eval` is unchanged: no network in demo (I8). With it on and the v5 pack complete, no live call happens either.
- Tail partition (`data/buckets/tail-v1.json`, part 2) for your E1 tail report comes next; I will message when the file and loader are fixed.
