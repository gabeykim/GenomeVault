# Agent C — app-ui-actions

**Mission:** everything the judges see and touch (F2 UI side, F5 view, F7, M9, M10).
**Owns:** `app.py`, `ui/`, `phone/`, `core/merge.py`, `core/actions.py`, `tests/C/`
**Provides to others:** the demo (P8).
**Depends on:** A's flags (G1), B's route + ledger (G2). Use mocks until then.

## Queue

1. `app.py` (FastAPI) + two-pane UI on mocks: flags and chat left, live ledger right, profile panel marked "on device".
2. `merge.py`: Answer + flags → personal answer; show state (`known`/`none_listed`/`no_data`) and trust tier; never "safe" (I7).
3. Swap to real `rules.check` after G1.
4. Swap to real `router.route` and `ledger.feed`. **Gate G2 (minimal UI).**
5. `phone/`: upload page over local HTTPS; receives reminders.
6. `actions.py`: pharmacist draft, one-page visit summary, reminders.
7. Demo mode toggle (I8) and a visible "offline" badge.
8. Polish beats S1–S7; on-screen "Demo, not medical advice". **Gate G3.**
