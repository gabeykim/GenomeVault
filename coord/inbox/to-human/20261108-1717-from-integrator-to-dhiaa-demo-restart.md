# For Dhiaa (demo machine): pull, restart demo-app, re-run the demo beats

- **From:** integrator (Gabe) · **To:** Dhiaa · **Time:** 2026-11-08 17:17
- **Re:** post-G4 merges #14–#17, G5 freeze (we freeze as soon as your beats pass — not waiting for 18:30)

The post-G4 polish is on **main `618fdb3`**, mini-gate green (make test 1291, `DEMO=1 make eval && python -m eval.gate` = 22/22, CI success):
- **A** #17: typo suggestions (`normalize.suggest`, behind **GV_FUZZY**, default OFF)
- **B** #15: tail partition + cover pin (**GV_TAIL**, **GV_DEMO_LIVE_FALLBACK**, default OFF)
- **C** #16: adaptive-questions UI fixes
- **D** #14: final figure pass

On the **demo machine**, please:
1. `git pull` on `main`.
2. Restart the demo app (your demo-app / `make demo`) and the local Ollama models.
3. Re-run the **demo-beat checks (S1–S7)** with the live vision + local models.
4. Keep **GV_FUZZY / GV_TAIL / GV_DEMO_LIVE_FALLBACK OFF** for the demo (they default OFF — just don't set them).

**Ping Gabe when the beats pass** and we freeze immediately.
