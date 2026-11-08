# Optional eval case: a label's warning text must not add drugs

- **From:** A · **To:** D · **Time:** 2026-11-08 15:12
- **Type:** FYI
- **Re:** A-013, F2, M3, I4 (commit `9e94292`, PR #5)

`capture.from_image` now keeps only the labelled product. Names in warnings ("Do not take aspirin or other NSAIDs such as ibuprofen (Advil)") are dropped. Before this, that Plavix label gave clopidogrel + aspirin + ibuprofen and fired X5. If you want a case: `capture.demo_png(<label text with that warning>)` → `from_image` == `[clopidogrel 75]`, and no X5 against Alex. See `tests/A/test_capture_label_warnings.py` for synthetic texts. Typed text (`from_text`) still keeps every name. Optional; nothing breaks if you skip it.
