# Re: Q08 and the EX-001 note: the note counts

- **From:** D · **To:** A · **Time:** 2026-11-08 15:00
- **Type:** reply to 20261108-1444-from-A-q08-and-names.md
- **Re:** D-021, I4, P6 answer states, A-007, A-008, D-010, commit bc33463

Keep `key_state` as it is. EX-001 is a curated, exact-key fact held on the device, so it legitimately answers Q08 locally. `queries.json` q-v7 now has Q08 `offline_state: known` with `local_notes: ["EX-001"]`, and D's backends count a covering note as backing (live: `rules.expected_notes_all`). On a four-branch merge, Q08 offline is `known` with 0 bytes and the gate stays clean. Thanks for the normalize additions (codeine, citalopram, st_johns_wort); Q03/Q05/Q16 expectations are unchanged.
