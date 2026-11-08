# Judging draft ready for review: docs/submission.md

- **From:** D · **To:** integrator (Dhiaa) · **Time:** 2026-11-08 15:30
- **Type:** reply to 20261108-1520-from-human-whats-left.md (item 4)
- **Re:** D-025, P8, commit on agent/D-eval (PR #4)

`docs/submission.md` is on PR #4: one-line pitch, problem, how it works (device / cloud split), the knowledge pack ("the cloud computes once for everyone; the device personalizes"), proof (red-team table, 0 vs 420 personal fields, 11 cloud calls for 20 questions, offline 11 → 18 of 20 with the pack, what the red team fixed), real vs demo, and team. About 720 words, paste-ready. Every figure is a PASS in the dry run with PR #6. Re-check against `slides/numbers.md` after G4.

Two notes:
- Personalization is described as rule-based, because in the merged build only `core/capture.py` calls a local model (the vision model). If `qwen3:8b` will personalize answers on stage, tell me and I'll change that line.
- Item 2 (priors for every v5 key) is already done: `partition_keys_without_prior` is 0 on v5. Items 5 (Q&A) and 6 (video script) are next.
