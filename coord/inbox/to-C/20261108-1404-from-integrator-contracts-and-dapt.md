# Integrator pass: capture/status accepted, stubs added, DAPT is informational (D-014, D-020, D-021)

- **From:** integrator (Gabe, backup) · **To:** C · **Time:** 2026-11-08 14:04
- **Type:** ruling
- **Re:** D-020, D-014, D-021, CONTRACTS, S2, S6, F8

- **Proposal accepted (D-020):** `capture.from_image` (owner A) and `cloud.status` (owner B) are now in CONTRACTS with stubs in `core/interfaces.py`. Call them from `app.py` (`POST /api/capture`, `GET /api/status`). The owners implement the real versions (A queue 6, B queue 9) — don't implement them in `app.py`.
- **Stub gap closed (D-014):** `core/interfaces.py` now has stubs for `normalize.to_ingredients` and `ledger.feed`. You can drop `app.py`'s local stand-ins and import from `interfaces` when you're ready.
- **DAPT note (D-021):** `aspirin|clopidogrel` is expected therapy after a stent — show it as an **informational UI note, never a warning or flag**. A will supply `data/rules/expected_combinations.json`. X5 (ibuprofen) is still a real flag.
