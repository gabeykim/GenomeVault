# PR #16: bug fix, Ask input didn't take clicks (C-029)

- **From:** C · **To:** integrator (Gabe) · **Time:** 2026-11-08 16:59
- **Type:** request (bug fix)
- **Re:** C-029, C-027, F7, S4, S6, G5

Cristian found that typing in Ask didn't work. The C-027 title caption, invisible once you scroll, still caught clicks just short of the end of the title screen, right over the Ask input. PR #16 makes it never catch clicks and sends the UI files with `Cache-Control: no-cache`, so cached copies don't keep the bug. CSS/JS plus one small middleware in `app.py`; no API or contract change. 1179 tests pass, CI running. Please merge before the stage run. After it merges, reload any open GenomeVault tab once.
