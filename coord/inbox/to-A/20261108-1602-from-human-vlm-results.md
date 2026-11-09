# Real vision-model test: 7/7 labels read correctly

- **From:** human (Dhiaa) · **To:** A · **Time:** 2026-11-08 16:02
- **Type:** heads-up
- **Re:** to-human/20261108-1523-from-A-g3-capture-results.md, D-029, F2, S2

Results on the demo laptop (M4 Pro, Ollama, `qwen2.5vl:7b`, `GV_OCR=vlm`, A's branch, C's 7 sample labels): **7/7 correct**. amoxicillin 500, aspirin 81, clopidogrel 75, ibuprofen 200, lisinopril 10, omeprazole 20, simvastatin 40. About **4.2 s per label** warm, 10.6 s for the first call (model load). Fully on-device.

The untested path from your 15:23 note is now tested; no change needed. Note for the env docs: existing `.env` files need `LOCAL_VLM_MODEL=qwen2.5vl:7b` added by hand (it was missing here, so the first run silently skipped the model and returned `[]` in 0.0 s).
