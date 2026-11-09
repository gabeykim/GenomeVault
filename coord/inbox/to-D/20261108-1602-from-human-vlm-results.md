# Numbers for the slides: on-device label reading 7/7, ~4 s

- **From:** human (Dhiaa) · **To:** D · **Time:** 2026-11-08 16:02
- **Type:** heads-up
- **Re:** D-029, S2, slides/numbers.md, docs/submission.md

Results on the demo laptop (M4 Pro, Ollama, `qwen2.5vl:7b`, `GV_OCR=vlm`, A's branch, C's 7 sample labels): **7/7 correct**. amoxicillin 500, aspirin 81, clopidogrel 75, ibuprofen 200, lisinopril 10, omeprazole 20, simvastatin 40. About **4.2 s per label** warm, 10.6 s for the first call (model load). Fully on-device.

Usable on a slide or in `docs/submission.md`: "Label photos are read by a 7B vision model on the laptop: 7/7 correct on the demo labels, ~4 s each, no network." State it as the demo label set (7 synthetic printed labels), not a general accuracy claim.
