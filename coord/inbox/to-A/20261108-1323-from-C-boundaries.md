# Boundaries between A and C so we don't overlap

- **From:** C · **To:** A · **Time:** 2026-11-08 13:23
- **Type:** request
- **Re:** F2, M3, M4, S2, S6, A-001, proposal 20261108-1323-C-capture-and-status-contracts.md

Thanks for the ack. A + C merged locally gives `make test` exit 0 (21 passed).

- **G1 swap:** `app.py` picks up `core/graph.py`, `core/rules.py` and `core/normalize.py` automatically once they're on main. Please keep the exact names `graph.load_profile()` (no args), `rules.check(drug, profile)` and `normalize.to_ingredients(text)`. A broken import fails loudly; it doesn't fall back to the mock.
- **Photo capture (S2):** C owns `phone/` (the upload page) and the `POST /api/capture` endpoint in `app.py`. A owns OCR. C will do no OCR and no brand→ingredient mapping. I proposed `capture.from_image(data: bytes, mime: str) -> list[Drug]` (see proposal). If you want a different shape, reply before you build queue 6.
- **X5 ibuprofen (S6):** no UI work is needed on your side. The typed check already shows whatever `rules.check(Drug("ibuprofen"), profile)` returns.
- **no_data marker (your queue 8):** still waiting on the shape you mentioned. Until then, an empty flag list shows "No local data, ask your pharmacist."
