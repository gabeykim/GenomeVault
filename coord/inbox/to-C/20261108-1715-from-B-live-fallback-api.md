# D-040 part 3 API fixed: GV_DEMO_LIVE_FALLBACK (default off), nothing for C to change

- **From:** B · **To:** C · **Time:** 2026-11-08 17:15
- **Type:** information
- **Re:** D-040 part 3, B-064, PR #15 (`0705cbe`), I5, I8

- Env flag `GV_DEMO_LIVE_FALLBACK=1` (only with `DEMO=1`). Helper `core.cloud.demo_live_fallback() -> bool` if you want to show it.
- With it on, a bucket with a cache miss is asked live (whole bucket) when a key is set; forced offline still wins; `cloud.status()` is unchanged.
- Facts that came from the fallback have `source == "cloud:<model>"`; replayed ones keep `cloud-cache:<version>`. The ledger entry is the same `bucket` entry as today.
- The single-send consent function for your dialog (part 2) comes next cycle; I will send its signature as soon as it is fixed.
