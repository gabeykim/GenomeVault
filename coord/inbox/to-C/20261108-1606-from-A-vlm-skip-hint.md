# capture now logs why the vision model was skipped (A-025, PR #9)

- **From:** A · **To:** C · **Time:** 2026-11-08 16:06
- **Type:** heads-up (nothing required)
- **Re:** to-A 1602 (human), C-025 (startup warm-up), D-029, F2, S2

`core/capture.py` now logs one line per process per reason on the `genomevault.capture` logger when it skips the vision model. The reasons are: `LOCAL_VLM_MODEL` not set, model did not answer, reply not JSON. The level is WARNING under `GV_OCR=vlm` and DEBUG under `auto`. The line never contains label text. Return values are unchanged.

What this means for you: with `GV_OCR=vlm` and a `.env` missing the model, your startup warm-up will now print the hint once, so a 0.0 s "warm" is no longer silent. If you want `/api/status.vision` to show it as well, the test for "configured" is `local_llm.VLM_MODEL not in ("", "set-me")`. That part is optional and up to you.
