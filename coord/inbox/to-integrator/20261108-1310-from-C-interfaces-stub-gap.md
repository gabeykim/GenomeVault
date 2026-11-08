# interfaces.py has no stub for ledger.feed or normalize.to_ingredients

- **From:** C · **To:** I · **Time:** 2026-11-08 13:10
- **Type:** heads-up
- **Re:** M12, CONTRACTS (`ledger.feed`, `normalize.to_ingredients`), C-001, commit c8a7839

CONTRACTS lists both functions as mocked until G1/G2, but `core/interfaces.py` has no stub for either. For now `app.py` carries its own labeled stand-ins, which switch off automatically when `core/ledger.py` / `core/normalize.py` exist. If you add stubs to interfaces.py, I'll switch to them. Nothing is blocked.
