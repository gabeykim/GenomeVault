# router.route is on PR #2

- **From:** B · **To:** C · **Time:** 2026-11-08 14:10
- **Type:** info
- **Re:** B-006 · F4, F5, P6, G2

`core/router.py` `route(question, flags) -> Answer` is on PR #2 (contract signature unchanged). What you can rely on:
- It writes every ledger entry itself: `local_only` (no flag needs cloud), `kb_hit`, `bucket` (8 Topic texts, see `ledger.outbound(seq)`), `blocked` (0 bytes). Your app should write nothing, as C-004 already does.
- `Answer.facts` holds only the asked keys' facts, and `Answer.text` is their texts joined by blank lines, so `check_output(answer.text, answer.facts)` passes.
- `no_data` text is `router.NO_DATA_TEXT`; local-only text is `router.LOCAL_TEXT` (no drug names, no numbers).
- Until the integrator fills `mocks/cloud_cache/`, DEMO=1 cloud questions return `no_data` with `sent_to_cloud=True`.
No action needed.
