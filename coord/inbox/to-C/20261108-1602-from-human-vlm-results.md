# Real vision-model test: 7/7, ~4 s per label; demo settings

- **From:** human (Dhiaa) · **To:** C · **Time:** 2026-11-08 16:02
- **Type:** request
- **Re:** D-029, S2, I8, rehearsal

Results on the demo laptop (M4 Pro, Ollama, `qwen2.5vl:7b`, `GV_OCR=vlm`, A's branch, C's 7 sample labels): **7/7 correct**. amoxicillin 500, aspirin 81, clopidogrel 75, ibuprofen 200, lisinopril 10, omeprazole 20, simvastatin 40. About **4.2 s per label** warm, 10.6 s for the first call (model load). Fully on-device.

For the demo:
1. **Show progress** while a photo is read ("Reading label on this laptop…"), since it takes ~4 s.
2. **Run the photo beat with `GV_OCR=vlm`** on the demo laptop, so S2 really uses the on-device vision model. In the default `auto` mode the bundled sample photos are read from their embedded text first and the model never runs; a judge who asks "is that real?" deserves a yes. Keep `auto`/embedded as the offline fallback.
3. **Warm the model** right before the demo (one throwaway photo) so the first read isn't 10 s.
