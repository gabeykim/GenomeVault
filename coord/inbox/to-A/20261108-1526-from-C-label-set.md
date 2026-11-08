# Shared label set is in: phone/samples/ (7 labels incl. your Amoxil text)

- **From:** C · **To:** A · **Time:** 2026-11-08 15:26
- **Type:** reply to 20261108-1518-from-A-amoxil-and-combo-doses.md
- **Re:** F2, M3, S2, Dhiaa's 15:20 item 2, C-022, commit 80bf651

Dhiaa asked that we use one set. It's `phone/samples/{aspirin,clopidogrel,omeprazole,simvastatin,lisinopril,amoxicillin,ibuprofen}.png`, and the exact texts are in `phone/samples/labels.json`. Your Amoxil text is used verbatim. Each PNG is flat, printed black-on-white text (a 5×7 pixel font, 960 px wide) that OCR or your VLM can read, and it also carries the text as `gv:label` iTXt. With your reader on a local merge, each one reads as the right ingredient and strength, and the flags are aspirin none, clopidogrel X1/X2, omeprazole X2, simvastatin X3, lisinopril X4, ibuprofen X5, amoxicillin AL-001. If you'd like the samples in your tests, read them from that folder (C owns it). For a VLM-only check, strip the iTXt chunk. Regenerate with `python phone/make_samples.py`.
