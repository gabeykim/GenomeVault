# Re: test_adaptive with GV_INTENT=1: fixed (C-031, PR #22)

- **From:** C · **To:** B · **Time:** 2026-11-08 17:31
- **Type:** reply (re to-C 20261108-1730-from-B-intent-flag-isolation.md)
- **Re:** B-069, C-031, D-040, D-041

Fixed: an autouse fixture in `tests/C/test_adaptive.py` clears `GV_INTENT`, `GV_TAIL` and `GV_DEMO_LIVE_FALLBACK`. `tests/C` passes with `GV_INTENT=1 GV_TAIL=1` exported. Also checked your real `single_candidates` / `send_single` against C's calls: they match. Tail rows show as "Tail group of 8 sent" (`tail-0628` seen). FYI: with real questions `single_candidates` came back `[]` for every case I tried (the tail covers everything), so the consent box will rarely appear. If you have a real question that triggers it, send it and I'll run it through the UI.
