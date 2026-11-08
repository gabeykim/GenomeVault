# G3 capture results: 6 labels clean, 1 false-drug path fixed

- **From:** A · **To:** human (Dhiaa / Gabe) · **Time:** 2026-11-08 15:23
- **Type:** reply to to-A/20261108-1516-from-human-skip-encryption.md
- **Re:** G3, F2, M3, S2, S6, I4

Encryption at rest: dropped. No `cryptography`, no `graph.py` change.

G3: `tests/A/test_capture_g3_labels.py` (56 tests, on PR #5 at `24c5148`). Full synthetic pharmacy labels for aspirin 81, clopidogrel 75, omeprazole 20, simvastatin 40, lisinopril 10 and amoxicillin 500 were run through embedded PNG/JPEG text, faked tesseract text and a faked vision-model reply. Each gives exactly the right Drug, which flags like the typed name (X1–X4; Amoxil → AL-001 only). Unknown or look-alike names give `[]`. Details are in A-015.

Fixed along the way: if a label's product line was unreadable, the drug named in its warning ("Avoid omeprazole") was taken as the product. It now gives `[]`.

Still untested: a real OCR engine or vision model on real photos. Neither tesseract nor Ollama is installed on this machine. If you want that checked before G3, start Ollama with `qwen2.5vl:7b` and set `LOCAL_VLM_MODEL` after PR #6 merges, then tell A. No action is needed otherwise.
