# Demo script note: let Sync finish before S6 Wi-Fi off (B-044)

- **From:** B · **To:** D · **Time:** 2026-11-08 17:05
- **Type:** info / script note
- **Re:** C-025, S6, F8, PR #10

With stage delays (`GV_DELAY_S=0.3,2.0`), Sync takes about 2 min. If Wi-Fi off (S6) is pressed before it finishes, the sync stops after the group in flight (`offline: true`). That's correct behaviour, and it explains C's one unreproduced partial Sync. Suggested script line: "wait for Sync done before Wi-Fi off". No change to the numbers or the gate.
