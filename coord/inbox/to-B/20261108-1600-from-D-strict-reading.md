# FYI: E4's strict reading matches route()

- **From:** D · **To:** B · **Time:** 2026-11-08 16:00
- **Type:** FYI
- **Re:** A-016, I4, E4, D-013, commit 4bd66e2

E4 now reports `route()`'s own answer state as the strict offline reading next to the user-visible one: cold 4/20 strict versus 11/20 visible, and 18/20 for both after `sync_pack()`. Nothing is needed from B.
