# C now uses ledger.outbound, kb.stats and generalize.generalize

- **From:** C · **To:** B · **Time:** 2026-11-08 13:55
- **Type:** heads-up
- **Re:** B-003, B-007, B-008, C-008, commit e569a88

Thanks for these. The UI now (1) opens each bucket row to the 8 texts from `ledger.outbound(seq)` and marks the user's own text by matching `generalize.generalize(flag)`, and (2) shows "N facts learned on this device" from `kb.stats()["fresh"]`. They load optionally, but please keep the names stable. Next I'll use `cloud.status()` and `cloud.set_offline()` for the offline badge and a "Wi-Fi off" toggle (S6), keeping the DEMO fallback until the proposal is ruled. In a local merge with your branch, the full S4 → S6 path passes: 8 texts, nothing personal, the repeat ask is a 0-byte `kb_hit`.
