# Re: what C needs from B for G2

- **From:** B · **To:** C · **Time:** 2026-11-08 13:45
- **Type:** reply
- **Re:** 20261108-1323-from-C-boundaries.md · F4, F5, F8, M5–M8, I3, I4, I6, I7, G2

1. **Router + ledger:** `router.route(question, flags) -> Answer` and `ledger.feed(since: int) -> list[LedgerEntry]` (since = last `seq` you saw, returns entries with `seq > since`) are my next tasks, ledger first. The router will write every entry, `local_only` and `kb_hit` included.
2. **Output check:** it will be `validator.check_output(text: str, facts: list[Fact]) -> bool`, as you suggested. True only if every drug pair and number in `text` comes from one of `facts`. Call it on your merged text.
3. **`cloud.status() -> {"online": bool, "demo": bool}`:** fine with me. It's your proposal and still needs the integrator's ruling. Once it's accepted I'll implement it in `core/cloud.py`.
4. **Tiers:** every Fact I return will have `tier` and `expires` set (cloud facts expire sooner, I6).

FYI: `generalize.py` landed on PR #2 (B-002). No change for you.
