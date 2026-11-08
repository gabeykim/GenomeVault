# B → C: cover traffic and delays are in (PR #2, commit bf8918b, B-009)

- To get P6.6 cover traffic in the app (G3), call `core.router.start_cover()` once at startup. It returns False if cover is already running. Call `router.stop_cover()` on shutdown. The interval comes from `GV_COVER_INTERVAL_S` (default 60 s, jittered 0.5–1.5×). For a lively demo ledger, try `start_cover(10)`.
- Cover sends show up in `ledger.feed()` with `kind="cover"`, `bytes_out > 0` and `personal_fields_sent == 0`. Please label them "cover traffic", separate from real `bucket` sends. `ledger.outbound(seq)` works for them too.
- Delays: in live mode every outbound request now waits 0.3–2.0 s at random, so a cloud question takes longer. Demo mode has no added delay unless you set `GV_DELAY_S`.
- Tests: nothing starts cover implicitly, so your tests are unaffected. If a test starts it, call `router.stop_cover()` in teardown.
