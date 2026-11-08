# Demo script (about 3.5 minutes, beats S1–S7 from PLAN P8)

The app has four tabs (C-009): Medications (S3, S6 ibuprofen), Ask (S4, S6 Q19/Q07), Actions (S6), My data (S2). The ledger stays on the right. Chips show the question text only (no Q-numbers), still exactly the texts in `eval/queries.json`. Screenshots from before C-009/C-010 are out of date.

Stage rules: pre-load everything, keep the demo-mode toggle ready (I8: the full demo runs with no network), and never improvise a question. Every question below is in `eval/queries.json`, so the eval has measured it.

| Beat | Time | Say | Do / show | Query |
| --- | --- | --- | --- | --- |
| S1 Hook | 20 s | "Alex just got a heart stent and five new prescriptions. One may not work for him, two could hurt him. His genome could tell us, but would you upload your genome to a chatbot?" | Title slide | — |
| S2 Capture | 30 s | "He photographs the labels on his phone." | Phone upload → meds appear on the PC; profile panel says "stays on this device" | — |
| S3 Local flags | 30 s | "Four problems, found on the device. Zero bytes sent." | **Medications** tab (the default): X1–X4 with severity and evidence; ledger shows 0 bytes, 0 personal fields (green) | Q01, Q02, Q06, Q11 |
| S4 Hybrid | 45 s | "What should I bring up with my cardiologist?" "The cloud gets fixed groups of 8 general questions. Only this screen knows which one was real." | Click the **Ask** tab (or open `/#ask`) and the first chip. As each bucket leaves, 8 identical blocks slide across the strand under the header (C-002) and the ledger row shows 8 cells; separate bucket entries, 0 personal fields; personalized answer citing Alex's results | Q18 |
| S5 Red team | 45 s | "We gave everything that left the laptop to an attacker. We don't claim privacy. We measure it." | `docs/charts/redteam.svg`: naive leaks everything, random decoys collapse on repeat, fixed buckets near 1 in 8 | — |
| S6 Learns, offline, acts | 45 s | "A related question: answered locally, 0 bytes." Then: "Wi-Fi off. Ibuprofen: still flagged." Then: "Pantoprazole instead of omeprazole? No local data for that exact pair, so it doesn't guess." | Q19 is a KB hit (its ↻ chip; the ledger adds a 0-byte `kb_hit` row and "facts learned" rises). Wi-Fi off, then on the **Medications** tab type **ibuprofen** into **"Check another medication"** (not the Ask tab): the medication check runs the local rules, so four high flags appear (bleeding with aspirin and with clopidogrel, kidney with lisinopril and eGFR), 0 bytes sent. Q07 says no data offline (fetches and stores its own key online); pharmacist draft (copy button) and the one-page visit summary (`/summary`) appear on the **Actions** tab (`/#actions`); the reminder reaches the phone. Say: "Even the calendar entry only says 'GenomeVault: Call your pharmacist', so no health detail lands in a synced calendar." (C-005) | Q19, typed "ibuprofen" (Q15's drug), Q07 |
| S7 Close | 15 s | "The more you use it, the less it needs the cloud. The same stack runs on a clinic edge server, or across hospitals without moving a genome." | `docs/charts/learning_curve.svg` | — |

## Before rehearsing: what must be true

Checked on a local merge of all four branches in demo mode (D-006). The privacy path works: Q18 sends b01 and b05, 0 personal fields. Three things still block beats:

| Needed | Blocks | Owner | Status |
| --- | --- | --- | --- |
| Recorded demo cloud answers in `mocks/cloud_cache/` | S4 personalized answer (every Ask is `no_data` today); S6 "learns" (Q19 re-sends b01 + b05 instead of a 0-byte KB hit) | Integrator (B's request, 13:50) | open |
| App shows all four X5 flags | S6 ibuprofen: the typed check shows only the kidney flag because flags are de-duplicated by id, and all four share id `X5` | C (A's note, A-003) | open |
| A's real rules on main | S3 and S6 flags come from A's tables, not mocks | Integrator at G1 (14:30) | PR #1 ready |

Rehearsal check: first run `python -m core.cloud check` (offline, B-013). It reports missing, wording-rejected (I7) and out-of-partition keys in the demo cache, and S4/S6 are ready only when it exits 0. Then restart `make demo` (the ledger is in memory), ask Q18 then Q19, and confirm Q19 adds a `kb_hit` row with 0 bytes. If it doesn't, the cache isn't loaded: switch to the backup video.

Backup: record the full run as video by G5 (20:15). Print `/summary` as a handout for judges.

The on-screen answer follows C's merge format (C-003): a general line (or the `none_listed` / `no_data` wording), one tier-labeled paragraph per fact ("AI-summarized, verify" or "Curated (source)"), a "For you" paragraph citing Alex's results, then a fixed closing line. Read the "For you" paragraph aloud in S4.

Do not say: "safe", "no interaction", "you should stop/start". Say: "no interaction listed in [source]", "worth asking your pharmacist".
Do not quote Alex's own joint-inference number. Cardiac is the most common synthetic scenario, so a blind guess already says cardiac. Use the population numbers.
