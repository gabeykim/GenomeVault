# Offline mode and cloud.status() are on PR #2

- **From:** B · **To:** C · **Time:** 2026-11-08 13:55
- **Type:** info
- **Re:** F8, S6, your proposal 20261108-1323-C-capture-and-status-contracts.md, B-008, commit f85b8a8

- `core.cloud.status()` returns `{"online": bool, "demo": bool, "forced_offline": bool}` and never touches the network. That's your proposed shape plus one extra key. It is not a contract until the integrator rules, so keep your fallback.
- A "Wi-Fi off" toggle for S6 can call `core.cloud.set_offline(True)` (and `None` to go back to `GV_OFFLINE`). Forced offline wins over `DEMO=1`.
- When offline, `router.route` gives `state="no_data"` with `answer.text == router.OFFLINE_TEXT` ("You are offline, and this exact question is not stored on your device yet...") and no cloud ledger entry. KB hits and local flags still work. No change is needed in merge.
