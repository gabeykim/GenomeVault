# capture.from_image now reads real label photos with the local VLM (D-029)

- **From:** A · **To:** C · **Time:** 2026-11-08 15:06
- **Type:** heads-up
- **Re:** D-020, D-029 (PR #6), F2, M3, S2, A-012, commit 271985d (PR #5)

Nothing to change in `app.py`. Same call, same `list[Drug]` result, still never raises. Once PR #6 is on main and the demo laptop sets `LOCAL_VLM_MODEL=qwen2.5vl:7b` with Ollama running, a photo with no embedded text goes to the local VLM. It returns brand, ingredient and strength, and A normalizes them exact-key. `[]` still means "show the typed box". Bundled demo PNGs still read first, with no model needed. The VLM call can take a few seconds, so a spinner on the photo upload would help. `GV_OCR=embedded` turns the model off if you need the old behavior.
