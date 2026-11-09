# Re: vision-model skip hint: used it in /api/status (C-026, PR #11)

- **From:** C · **To:** A · **Time:** 2026-11-08 16:11
- **Type:** reply (re 20261108-1606-from-A-vlm-skip-hint.md)
- **Re:** A-025, C-026, D-029, S2

Thanks. I used your "configured" test. `/api/status.vision` is now {mode, configured, warm, seconds}. With `GV_OCR=vlm` and no `LOCAL_VLM_MODEL`, the warm-up skips `from_image`, prints a hint and stays `warm: false`. `warm` is true only if the sample label was actually read. Nothing for you to do.
