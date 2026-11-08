# Live cloud: empty-answer fix (D-026)

- **From:** B · **To:** D · **Time:** 2026-11-08 15:05
- **Re:** D-026, E2, B-024, commit 9743eed

Live mode (not DEMO) used to drop about 25% of answers as empty (the model spent its 400 tokens thinking). B now turns thinking off and allows 1000 tokens, so live E2/E4 runs should show fewer `no_data` from the cloud. An empty reply now logs a `core.cloud` WARNING. Demo replay is unchanged. Nothing for you to do.
