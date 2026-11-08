# capture.from_image is real (A-006)

- **From:** A · **To:** C · **Time:** 2026-11-08 14:30
- **Type:** FYI (Advances of D-020)
- **Re:** D-020, F2, M3, S2, A-006

`core/capture.py` is on PR #1 (commit `f9db84a`) with the exact CONTRACTS signature `from_image(data: bytes, mime: str) -> list[Drug]`.

- It returns `[]` for anything unreadable and never raises, so on `[]` your phone page can show the typed box. `capture.from_text(text)` is the typed path (same normalizer as `normalize.to_ingredients`).
- Pass the upload's content type as `mime`. The bytes decide the image type, and the MIME only has to start with `image/`.
- No OCR engine is bundled. Images become readable in two ways: (a) embedded label text (a PNG text chunk `gv:label`, or a JPEG comment starting `gv:label`); (b) a local `tesseract`, if the integrator installs it. A plain camera photo without tesseract gives `[]`.
- For the S2 demo, `capture.demo_png("CLOPIDOGREL 75 MG TABLET\nGeneric for: PLAVIX")` returns PNG bytes that read as `[Drug(clopidogrel, 75)]`. For S6, `demo_png("IBUPROFEN 200 MG")` reads as ibuprofen 200. If you want static sample images, you can write these into `phone/` (yours). Keep the text synthetic (I1).
- `GV_OCR=off|embedded|tesseract|auto` (default `auto`) if you need to force a path in tests.

Nothing you have to do. Until G3 the interfaces stub stays as it is.
