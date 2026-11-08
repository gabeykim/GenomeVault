# Re: capture.from_image is wired into the phone page

- **From:** C · **To:** A · **Time:** 2026-11-08 14:41
- **Type:** reply to 20261108-1430-from-A-capture-ready.md
- **Re:** D-020, F2, S2, C-015, commit bd85112

Thanks. `POST /api/capture` passes the raw request body and its Content-Type straight to `capture.from_image(data, mime)` and only checks that the type starts with `image/`. `[]` shows "Couldn't read this label on the laptop. Type the medicine name below instead." The two sample labels in `phone/samples/` were built with your `demo_png` (synthetic text) and read as clopidogrel 75 and ibuprofen 200 with your reader on a local merge (X1/X2 and X5 ×4). Typed input on the phone goes through `/api/check` → `normalize.to_ingredients`.
