# capture: one-time hint when the vision model is skipped (A-025, PR #9)

- **From:** A · **To:** D · **Time:** 2026-11-08 16:06
- **Type:** heads-up (optional docs line)
- **Re:** to-A 1602 (human), D-014, D-029, S2

No numbers change: eval and gate inputs stay the same, and `from_image` returns the same values.

Optional, for the env/setup docs you own: the human found that **existing `.env` files need `LOCAL_VLM_MODEL=qwen2.5vl:7b` added by hand**. `.env.example` already has the line. Without it, `GV_OCR=vlm` read nothing in 0.0 s. Capture now logs a WARNING saying so, but a setup line in the docs would stop it happening at all.
