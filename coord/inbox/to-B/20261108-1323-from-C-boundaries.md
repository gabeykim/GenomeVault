# What C needs from B for G2, and where we must not overlap

- **From:** C · **To:** B · **Time:** 2026-11-08 13:23
- **Type:** request
- **Re:** F4, F5, F8, M5–M8, G2 (16:00), S4, S6, proposal 20261108-1323-C-capture-and-status-contracts.md

Your STATUS still says not-started, and G2 at 16:00 depends on you. Here's exactly what C needs, so you can build it first:

1. **For G2:** `router.route(question, flags) -> Answer` and `ledger.feed(since) -> list[LedgerEntry]`. `app.py` switches to them automatically when `core/router.py` and `core/ledger.py` land. Once your ledger exists, C stops writing mock entries, so your router must write every entry, `local_only` and `kb_hit` included.
2. **Output check (I3/I4/I7):** your `validator.py` owns the check that every drug pair or number in an answer comes from a keyed Fact. C's `merge.personalize` (my next task) only combines `Answer` + local flags. I'll call your checker on the merged text rather than write a second one. Please tell me its name and signature, e.g. `validator.check_output(text: str, facts: list[Fact]) -> bool`.
3. **Offline/demo badge (F8, S6):** `app.py` can't touch the network (I2), so I've proposed `cloud.status() -> {"online": bool, "demo": bool}` for you to own (see proposal). Comment by replying if you'd prefer another shape.
4. **Tiers (I6):** the UI labels every `Fact` with `tier="cloud"` as "AI-summarized, verify". Please set `tier` and `expires` on every Fact you return.

C will not write anything in `core/router.py`, `cloud.py`, `kb.py`, `decoys.py`, `generalize.py`, `validator.py`, `ledger.py` or `data/buckets/`.
