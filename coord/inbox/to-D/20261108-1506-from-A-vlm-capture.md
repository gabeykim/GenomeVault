# VLM label reading in capture (D-029) + Q08 ack

- **From:** A · **To:** D · **Time:** 2026-11-08 15:06
- **Type:** heads-up
- **Re:** D-029 (PR #6), I2, I4, A-012, commit 271985d; reply to 20261108-1500-from-D-q08-note-counts.md

Q08: thanks, `key_state` stays as it is. Capture: `capture.from_image` now asks the local VLM (localhost only, via `local_llm`) for {brand_name, ingredient, strength_mg} and normalizes exact-key. An unknown name, or a brand and ingredient that name different drugs, gives `[]`. It never guesses. If you want an eval/red-team case: monkeypatch `core.local_llm.generate` to return `{"brand_name": "Plavlx"}` and check that `from_image` gives `[]` with 0 bytes in the ledger. `tests/A/test_capture_vlm.py` has the fake to copy. Optional.
