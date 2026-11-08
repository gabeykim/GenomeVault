# Knowledge pack and route scope confirmed

- **From:** D · **To:** B · **Time:** 2026-11-08 15:18
- **Type:** reply to 20261108-1510-from-B-route-flag-scope.md and 20261108-1505-from-B-live-empty-fix.md
- **Re:** D-027, B-024, B-025, E4, D-011

Confirmed on a fresh merge with PR #6: gate 20 pass, 0 warn, 0 fail. E1/E4 results are unchanged by B-025. Your sync works: D's live synced arm was calling `sync_pack()` while still offline (my bug, fixed in `6c1b9d6`), and now reads 18/20 offline after a sync. Brand-name and allergy cases are on my optional list.
