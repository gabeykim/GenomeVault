# B → D: cover traffic and delays are in (PR #2, commit bf8918b, B-009)

- `core.router.send_cover()` sends one bucket drawn uniformly from the fixed v1 partition (12 buckets). The choice is independent of the question, which is what E1's joint-inference attacker should model. `start_cover(interval_s)` runs it on a schedule; see `ledger.feed()` for `cover` entries.
- P6.4 delays: in live mode each request waits uniform(`GV_DELAY_S`), default 0.3–2.0 s. For E3 latency, report hybrid with the default delays and note the mean of ≈1.15 s per request. Set `GV_DELAY_S=0,0` for a no-delay baseline. In demo mode the delay is 0.
- Cover answers go into the KB. For E2/E4 cold runs, don't run cover (or call `kb.clear()` after stopping it).
- I'm still happy to rebalance buckets by frequency if you send per-bucket numbers from E1's statistical attacker.
