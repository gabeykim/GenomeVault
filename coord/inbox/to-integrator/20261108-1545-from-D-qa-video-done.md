# Judge Q&A and backup video script ready (items 5 and 6)

- **From:** D · **To:** integrator (Dhiaa) · **Time:** 2026-11-08 15:45
- **Type:** reply to 20261108-1520-from-human-whats-left.md (items 5 and 6)
- **Re:** P8, D-025, D-027, commit 5112526 (PR #4)

- **`slides/judge_qa.md`:** your five answers are in (why the cloud, is it really 1 in 8, Ollama vs NPU, encryption at rest, pack size), plus "Isn't syncing the pack a leak?", which cites B's same-for-all test. Stale simulated figures are replaced with the integrated dry run. The pack-size answer (about 500,000 pairs, about half a GB) is labelled an estimate. The encryption answer says the app relies on OS full-disk encryption today, as you wrote; please correct it if that's not how the demo laptop is set up.
- **`slides/video_script.md`:** 3:00, S1–S7 with narration, on-screen steps, a pre-record checklist (`python -m core.cloud check`, a fresh `DEMO=1 GV_COVER_INTERVAL_S=10 make demo`, phone pairing) and fallbacks. I checked the steps on a merged demo build: Q18 is answered from the pack, a repeat is a 0-byte KB hit, Plavix resolves with X1/X2, and 0 personal fields left. Q18 sends one group instead of two once cover traffic has prefetched one; the script says so. The timings are D's estimates until C's rehearsal. **The video has to be recorded before the 18:30 freeze.**
