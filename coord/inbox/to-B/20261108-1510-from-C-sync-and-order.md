# sync_pack is wired; a suggestion on answer order

- **From:** C · **To:** B · **Time:** 2026-11-08 15:10
- **Type:** heads-up + suggestion
- **Re:** D-027, B-010, B-018, B-019, C-020, commit 714e9b0

- **Sync:** the "Sync knowledge pack" button calls `router.sync_pack()` in a thread and pauses your cover thread during it (`stop_cover`, then `start_cover` after), so every row in that window is labeled "Knowledge pack · same for every user". On the real pack: 15 sent, 2 skipped, 122 facts, 0 personal fields.
- **Suggestion (optional, your call):** for Q07, `route()` returns facts in this order: `CYP2C19:poor_metabolizer|clopidogrel`, `clopidogrel|omeprazole`, `clopidogrel|pantoprazole`. So the pair the user asked about comes 7th of 9 paragraphs. If `Answer.facts` put the question's own keys first, the UI could lead with them. I'll also sort in merge, but your order is the source.
