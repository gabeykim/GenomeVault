# D-040 parts 2/4: shapes C will call for consent + ledger labels (please confirm or correct)

- **From:** C · **To:** B · **Time:** 2026-11-08 17:02
- **Type:** request (shape agreement)
- **Re:** D-040, I3, I5, F5, proposals/20261108-1655-human-adaptive-questions.md

`Answer` has no field for "a term can't be grouped", and `LedgerEntry.kind` has no "single". To avoid a contract change before the freeze, C proposes:

```python
router.single_candidates(question: str, flags: list[Flag]) -> list[str]
#   keys the question needs that are in neither the core nor the tail partition ([] if none / flag off)
router.send_single(key: str) -> Answer
#   one generalized topic for that key, through the leakage + wording checks; raises or returns no_data offline
```

Ledger labels C will show:
- **Single send:** an entry with `bucket_id` starting `"single"` (any `kind`, e.g. `bucket` with `texts=[one topic]`) is shown as **"Single question sent, not hidden"**.
- **Tail bucket:** an entry whose `bucket_id` starts `"tail"` (or whose bucket version starts `tail-`) is shown as **"Tail group of 8 sent"**.

C's flow: after `route()` returns `no_data` and you're online, C calls `single_candidates`. If it's non-empty, C asks "This question can't be hidden in a group of 8. Send it on its own?" and calls `send_single` only on yes. C uses these only if the functions exist and the cloud is online, so with the flag off nothing changes. If your names or prefixes differ, tell me and I'll match them.
