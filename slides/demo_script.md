# Demo script (about 3.5 minutes, beats S1–S7 from PLAN P8)

The app has four tabs (C-009): Medications (S3, S6 ibuprofen), Ask (S4, S6 Q19/Q07), Actions (S6), My data (S2). The ledger stays on the right. Chips show the question text only (no Q-numbers), still exactly the texts in `eval/queries.json`. Screenshots from before C-009/C-010 are out of date.

Live delays: keep demo mode for the stage run. With B's default P6.4 delays (`GV_DELAY_S=0.3,2.0`), each bucket is 8 requests paused one after another, so a question that sends buckets took a median of 18.8 s on the merged build (D-008); demo mode defaults to no delay.

Stage rules: pre-load everything, keep the demo-mode toggle ready (I8: the full demo runs with no network), and never improvise a question. Every question below is in `eval/queries.json`, so the eval has measured it.

| Beat | Time | Say | Do / show | Query |
| --- | --- | --- | --- | --- |
| S1 Hook | 20 s | "Alex just got a heart stent and five new prescriptions. One may not work for him, two could hurt him. His genome could tell us, but would you upload your genome to a chatbot?" | Title slide | — |
| S2 Capture | 30 s | "He photographs the labels on his phone. The photo is read on the laptop, not in the cloud, and isn’t kept." | Laptop: `bash phone/serve_https.sh`, then Actions → **Use your phone** shows a 6-character code; the phone opens the printed address (accept the certificate once) and types the code. Tap the **CLOPIDOGREL 75 MG** sample label → the phone asks “Is that right?” → **Yes, check it**: X1 and X2 show in red on the phone, and the laptop’s Medications tab shows “From your phone · Clopidogrel 75 mg · 2 flags” (C-015, C-020). If venue Wi-Fi isolates devices, use a phone hotspot. | — |
| S3 Local flags | 30 s | "Four problems, found on the device. Zero bytes sent." | **Medications** tab (the default): X1–X4 with severity and evidence; ledger shows 0 bytes, 0 personal fields (green) | Q01, Q02, Q06, Q11 |
| S4 Hybrid | 45 s | "What should I bring up with my cardiologist?" "The cloud gets fixed groups of 8 general questions. Only this screen knows which one was real." | Click the **Ask** tab (or open `/#ask`) and the first chip. Point at the "Cover traffic" rows in the ledger (C-014): "Decoys go out even when Alex isn't asking." Launch with `GV_COVER_INTERVAL_S=10` for a livelier stage run, or `GV_COVER=0` for a quiet rehearsal. As each bucket leaves, 8 identical blocks slide across the strand under the header (C-002) and the ledger row shows 8 cells; separate bucket entries, 0 personal fields; personalized answer citing Alex's results | Q18 |
| S5 Red team | 45 s | "We gave everything that left the laptop to an attacker. We don't claim privacy. We measure it." | `docs/charts/redteam.svg`: naive leaks everything, random decoys collapse on repeat, fixed buckets near 1 in 8 | — |
| S6 Learns, offline, acts | 45 s | "Ask it again: answered on the device, 0 bytes." "Sync the knowledge pack: the same download for every user, so it reveals nothing." "Now offline. Still answering." "Pantoprazole instead of omeprazole? No local data for that exact pair, so it doesn’t guess." | On the Ask tab: ask Q18 (2 groups sent), then **Q18 again** (0-byte `kb_hit`). In the ledger panel click **Sync knowledge pack** (rows read “Knowledge pack · same for every user”, D-027). Click the **Online** switch so it reads **Offline** (C-013). Ask Q07, Q15 or Q19: answered on device, 0 B. Type **pantoprazole** (“No local entry for pantoprazole with clopidogrel…”). On the Medications tab, **ibuprofen** shows four high X5 flags, 0 B. Actions tab (`/#actions`): pharmacist draft (copy button), one-page `/summary`; the reminder reaches the phone. Say: "Even the calendar entry only says ‘GenomeVault: Call your pharmacist’." Bonus if time: type **Amoxil** → a penicillin allergy flag, computed locally, 0 bytes (A-011). | Q18 ×2, Q07/Q15/Q19, pantoprazole, ibuprofen |
| S7 Close | 15 s | "The more you use it, the less it needs the cloud. The same stack runs on a clinic edge server, or across hospitals without moving a genome." | `docs/charts/learning_curve.svg` | — |

## Before rehearsing: what must be true

Checked on a local merge of all four branches in demo mode (D-006). The privacy path works: Q18 sends b01 and b05, 0 personal fields. Three things still block beats:

| Needed | Blocks | Owner | Status |
| --- | --- | --- | --- |
| Recorded demo cloud answers in `mocks/cloud_cache/` | S4 personalized answer (every Ask is `no_data` today); S6 "learns" (Q19 re-sends b01 + b05 instead of a 0-byte KB hit) | Integrator (B's request, 13:50) | open |
| App shows all four X5 flags | S6 ibuprofen: the typed check shows only the kidney flag because flags are de-duplicated by id, and all four share id `X5` | C (A's note, A-003) | open |
| A's real rules on main | S3 and S6 flags come from A's tables, not mocks | Integrator at G1 (14:30) | PR #1 ready |

Rehearsal check: first run `python -m core.cloud check` (offline, B-013). It reports missing, wording-rejected (I7) and out-of-partition keys in the knowledge pack (`mocks/cloud_cache/`, D-027), and S4/S6 are ready only when it exits 0. On the merge with PR #6 it does: 136/136 usable. Then restart `make demo` (the ledger is in memory), ask Q18 then Q19, and confirm Q19 adds a `kb_hit` row with 0 bytes. If it doesn't, the cache isn't loaded: switch to the backup video.

Backup: record the full run as video before the G5 freeze (18:30, PLAN v1.3); the project draft is saved at 19:00 and demos start at 20:00. Print `/summary` as a handout for judges.

The on-screen answer follows C's merge format (C-003): a general line (or the `none_listed` / `no_data` wording), one tier-labeled paragraph per fact ("AI-summarized, verify" or "Curated (source)"), a "For you" paragraph citing Alex's results, then a fixed closing line. Read the "For you" paragraph aloud in S4.

Do not say: "safe", "no interaction", "you should stop/start". Say: "no interaction listed in [source]", "worth asking your pharmacist".
Do not quote Alex's own joint-inference number. Cardiac is the most common synthetic scenario, so a blind guess already says cardiac. Use the population numbers.
