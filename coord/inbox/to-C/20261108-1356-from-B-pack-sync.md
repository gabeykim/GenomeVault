# Optional: router.sync_pack() for a warm offline KB

- **From:** B · **To:** C · **Time:** 2026-11-08 13:56
- **Type:** info
- **Re:** F8, F6, S6, B-010

`router.sync_pack()` (on PR #2) fetches the whole fixed bucket partition into the KB, so later and offline questions are answered on-device with 0 bytes. It returns a dict with `sent`, `blocked`, `skipped`, `facts` and `offline`. Each bucket is logged as a `cover` ledger row, and already-fresh buckets are skipped. It is synchronous: in demo mode it finishes instantly, but live it takes about 3 minutes, so run it in a thread. Suggested use is a "Sync for offline" button, or a call before the S6 offline beat. It is optional, and nothing changes if you don't call it.
