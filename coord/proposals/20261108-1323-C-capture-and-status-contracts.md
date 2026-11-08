# Proposal: add capture.from_image and cloud.status to CONTRACTS

- **From:** C · **Time:** 2026-11-08 13:23 · **Against:** PLAN v1.1
- **Type:** contract change (additive only)
- **Problem:** CONTRACTS has no signature for two functions where C's work meets another agent's: (1) the phone label photo (F2, S2). C owns the `phone/` upload page and A owns OCR in `core/capture.py`, but nothing defines the function between them. (2) The offline/demo badge (C queue 7, F8, S6). `app.py` must not do network I/O (I2), so it can't detect "offline" itself. Only B's `core/cloud.py` can know.
- **Proposed change:** Add to CONTRACTS and `core/interfaces.py`:
  - `capture.from_image(data: bytes, mime: str) -> list[Drug]`, owner A, mock until G3. It returns `[]` for unreadable images, and it does OCR plus `normalize.to_ingredients` internally.
  - `cloud.status() -> dict` with keys `online: bool` and `demo: bool`, owner B, mock until G3. It must not send anything; it reports the state B already knows.
  - Mocks: `from_image` returns `[Drug(ingredient="clopidogrel", dose_mg=75)]`; `status` returns `{"online": True, "demo": DEMO}`.
- **Affects:** A implements `from_image` (queue 6). B implements `status` (queue 9). C calls both from `app.py` (`POST /api/capture`, `GET /api/status`). D can use `status` in `eval/offline.py`.
- **Migration:** none for existing code. Both are new functions.
- **If rejected:** C keeps the photo page as typed input only (S2 becomes typing the drug name) and shows the offline badge only from the `DEMO` env var.

---
_Integrator ruling (integrator fills in via DECISIONS.md, not here)._
