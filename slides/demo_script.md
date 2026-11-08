# Demo script (about 3.5 minutes, beats S1–S7 from PLAN P8)

Stage rules: pre-load everything, keep the demo-mode toggle ready (I8: the full demo runs with no network), and never improvise a question. Every question below is in `eval/queries.json`, so the eval has measured it.

| Beat | Time | Say | Do / show | Query |
| --- | --- | --- | --- | --- |
| S1 Hook | 20 s | "Alex just got a heart stent and five new prescriptions. One may not work for him, two could hurt him. His genome could tell us, but would you upload your genome to a chatbot?" | Title slide | — |
| S2 Capture | 30 s | "He photographs the labels on his phone." | Phone upload → meds appear on the PC; profile panel says "stays on this device" | — |
| S3 Local flags | 30 s | "Four problems, found on the device. Zero bytes sent." | X1–X4 with severity and evidence; ledger shows `local_only`, 0 bytes | Q01, Q02, Q06, Q11 |
| S4 Hybrid | 45 s | "What should I bring up with my cardiologist?" "The cloud gets fixed groups of 8 general questions. Only this screen knows which one was real." | As each bucket leaves, 8 identical blocks slide across the strand under the header (C-002) and the ledger row shows 8 cells; separate bucket entries, 0 personal fields; personalized answer citing Alex's results | Q18 |
| S5 Red team | 45 s | "We gave everything that left the laptop to an attacker. We don't claim privacy. We measure it." | `docs/charts/redteam.svg`: naive leaks everything, random decoys collapse on repeat, fixed buckets near 1 in 8 | — |
| S6 Learns, offline, acts | 45 s | "A related question: answered locally, 0 bytes." Then: "Wi-Fi off. Ibuprofen: still flagged." Then: "Pantoprazole instead of omeprazole? No local data for that exact pair, so it doesn't guess." | Q19 is a KB hit; Wi-Fi off → Q15 flags X5; Q07 says no data offline (fetches and stores its own key online); pharmacist draft and reminder go to the phone | Q19, Q15, Q07 |
| S7 Close | 15 s | "The more you use it, the less it needs the cloud. The same stack runs on a clinic edge server, or across hospitals without moving a genome." | `docs/charts/learning_curve.svg` | — |

Backup: record the full run as video by G5 (20:15).

Do not say: "safe", "no interaction", "you should stop/start". Say: "no interaction listed in [source]", "worth asking your pharmacist".
Do not quote Alex's own joint-inference number. Cardiac is the most common synthetic scenario, so a blind guess already says cardiac. Use the population numbers.
