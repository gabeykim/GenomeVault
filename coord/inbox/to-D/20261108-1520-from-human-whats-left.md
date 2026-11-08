# What's left for D: real numbers, slides, and the 19:00 judging draft (G4 18:15)

- **From:** human (Dhiaa) · **To:** D · **Time:** 2026-11-08 15:20
- **Type:** request
- **Re:** BRIEF D queue 5–7, E1–E4, S5, S7, PLAN v1.3 (PR #6: D-025 gates, D-027 pack), G4

Your evals, charts, slides and docs are in place, and your dry run already uses 18:15; good. Remaining:

1. **G4 (18:15): run `make eval` on integrated main** once PRs #2, #3, #5 and #6 merge. The knowledge pack is in `mocks/cloud_cache/` (136/136 on partition v5), so E2/E4 should run on real answers. E4 should report **cold vs synced** offline coverage; E1 should show `sync_pack` traffic scoring at chance, since it is the same for every user.
2. **E1 statistical attacker:** `eval/fixtures/universe_v1.json` priors still need to cover every v5 key (your own run_all note) before E1 statistical numbers are quoted on a slide. If there isn't time, show the uniform-prior result and label the prior "illustrative".
3. **Numbers into slides:** fill `slides/numbers.md` and the pitch from the G4 results: attacker accuracy (none / random decoys / fixed buckets vs 1-in-8), cloud-call rate falling over the learning curve, offline coverage cold vs synced, latency and cost (hybrid vs local-only vs cloud-only).
4. **Judging draft (due 19:00, finalists are chosen from it):** write `docs/submission.md` for the AGI House project page: a one-line pitch, the problem, how it works (device / cloud split), the knowledge pack ("the cloud computes once for everyone; the device personalizes"), proof (the two strongest charts), what's real vs demo, and the team. Keep it short enough to paste.
5. **Judge Q&A additions** (`slides/judge_qa.md`): "Why the cloud at all?" (it builds the pack once for everyone; live calls only for open-ended or new questions); "Is it really 1 in 8?" (only with frequency-balanced buckets; that's what E1 measures); "Why Ollama, not the NPU?" (portable for the demo; the model client is one localhost URL, so an NPU runtime is a config change); "Is data encrypted at rest?" (OS full-disk encryption via FileVault/BitLocker today; app-level encryption with hardware-backed keys on the roadmap); "How big does the pack get?" (136 keys today; ~500,000 pairs for the top 1,000 drugs, about half a GB, built once).
6. **Backup video script** for G5 (18:30): S1–S7 in about 3 minutes, using C's rehearsal timings.
