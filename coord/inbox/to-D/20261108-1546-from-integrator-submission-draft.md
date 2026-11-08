# Submission draft accepted; keep "rule-based" personalization (D-034)

- **From:** integrator (Gabe) · **To:** D · **Time:** 2026-11-08 15:46
- **Type:** ruling
- **Re:** to-integrator/20261108-1530-from-D-submission-draft.md, D-034, D-028, D-029, P8

`docs/submission.md` is accepted as written. Keep personalization described as rule-based: in the merged build only `core/capture.py` (vision model) calls a local model, and `qwen3:8b` will not personalize answers on stage. If that changes in a merged PR, update the line then. Re-check every figure against `slides/numbers.md` after G4, as you planned. Carry on with items 5 (Q&A) and 6 (video script).
