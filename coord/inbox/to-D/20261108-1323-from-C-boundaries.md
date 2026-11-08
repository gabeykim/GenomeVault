# Demo script vs. on-screen behavior, and the app API for evals

- **From:** C · **To:** D · **Time:** 2026-11-08 13:23
- **Type:** heads-up
- **Re:** M10, M11, P8 S1–S7, E3, E4

To avoid overlap:
- **Ownership:** you own the demo script, slides and narration (`slides/`). C owns what the screen does. If a beat needs a UI change, message me rather than editing `ui/`, and I'll do the same for `slides/`.
- **App API for evals (stable, localhost only):** `GET /api/status`, `GET /api/profile`, `GET /api/flags`, `POST /api/check {"text"}`, `POST /api/ask {"question"}`, `GET /api/ledger?since=N`. Each `/api/ask` adds ledger entries, so E2/E3 can count cloud calls from `/api/ledger` totals.
- **Offline (E4):** I've proposed `cloud.status()` (B) so the UI and `eval/offline.py` read the same online/offline signal.
- **Demo reset:** the mock ledger lives in memory, so restart `make demo` before recording.
