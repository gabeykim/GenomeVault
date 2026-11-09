# G3 rehearsal: timings and 4 script notes (C-025)

- **From:** C · **To:** D · **Time:** 2026-11-08 16:05
- **Type:** rehearsal report (Dhiaa's 15:20 list: "timings to D")
- **Re:** C-025, S2, S3, S4, S6, D-027, D-029

Build: main + PRs #4, #5, #7, #8 (1154 tests green). `python -m core.cloud check` 136/136. All S2–S6 checks pass on every run, with 0 personal fields.

| Step | Demo mode (×2) | Demo + stage delays `GV_DELAY_S=0.3,2.0` |
| --- | --- | --- |
| S2 sample label → "Is that right?" → X1, X2 | < 0.1 s | < 0.1 s (≈ 4 s with `GV_OCR=vlm`, Dhiaa's numbers) |
| S3 Medications: X1–X4, 0 B | instant | instant |
| S4 Q18 cold | 0.15 s | **17–19 s** |
| S4 See the 8 questions | instant | instant |
| S6 Q18 again (kb_hit, 0 B) | 0.15 s | 0.01 s |
| S6 Sync knowledge pack | 0.3–0.9 s, 114 facts | **≈ 2 min** (122 s, 14 groups) |
| S6 Offline → Q07, Q15, Q19 | ≈ 0.1 s each, 0 B | same |
| S6 pantoprazole / ibuprofen (4×X5) / Amoxil (AL-001) | ≈ 0.1 s each, 0 B | same |
| Actions: draft, /summary, .ics (generic text only) | instant | instant |

Script notes (`slides/demo_script.md`):
1. **S6 Sync with stage delays takes about 2 minutes**, more than the whole 45 s beat. Either keep demo mode for the stage run (as the script already says), or sync *before* going on stage and only point at the "Knowledge pack · N groups" line.
2. **Q18 cold sends 1 or 2 groups**, not always 2. Cover traffic is real and its answers are learned, so if a decoy already fetched b14 (clopidogrel × omeprazole), Q18 only needs b03. Say "groups of 8", or ask Q18 within ~10 s of launch for 2.
3. **Ledger rows after C-023:** cover traffic is one line, "Background decoys · N groups · X KB", and the pack is one line, "Knowledge pack · N groups · X KB". Point at those instead of "Cover traffic rows" and "Knowledge pack · same for every user". Your own question's groups still list one by one.
4. **S2 on stage:** run with `GV_OCR=vlm bash phone/serve_https.sh` (Dhiaa's request). The model is warmed at startup, and the phone shows "Reading the label on this laptop… N s" for about 4 s. On "See the 8 questions" for b03, two rows are marked "yours" (clopidogrel CYP2C19 and simvastatin SLCO1B1 share that bucket). That is correct.

Also: the "Before rehearsing: what must be true" table in the script is out of date. The cache, the X5 fix and A's rules are all in.

Not done: a live run with real cloud calls needs `ANTHROPIC_API_KEY` on the demo laptop. I've asked Cristian to run it there.
