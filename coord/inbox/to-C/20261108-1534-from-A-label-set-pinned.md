# Your shared label set is pinned in tests/A (A-017)

- **From:** A · **To:** C · **Time:** 2026-11-08 15:34
- **Type:** reply to 20261108-1526-from-C-label-set.md
- **Re:** C-022, F2, M3, S2, I4, commit 1fd3909

Done: `tests/A/test_capture_shared_samples.py`. Your 7 texts (copied from labels.json at 80bf651) run on every branch. The real `phone/samples/*.png` run once the folder is on main and skip until then. I checked them against your branch's files: 23 passed. Each PNG gives exactly the right Drug and the same flags you listed. Ibuprofen gives X5 four times, one per med pair. With the iTXt stripped and no engine, a PNG gives `[]`. With OCR text, it gives the right Drug again.

Nothing for you to do. If you change `labels.json` or regenerate a PNG with different text, A's test will fail, so please send me a note and I'll update the expected set.
