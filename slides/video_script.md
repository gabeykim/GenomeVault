# Backup video script (about 3:00, record before the G5 freeze at 18:30)

The video is the fallback if the live demo fails on stage. It's the same story as `slides/demo_script.md`, tightened to 3 minutes. Timings are D's beat estimates; adjust them after C's rehearsal. Every figure is from the G4 dry run (20 pass, 0 warn, 0 fail); re-check against `slides/numbers.md` before recording.

## Before you hit record

1. On the integrated build: `python -m core.cloud check` exits 0 (knowledge pack 136/136).
2. Start the app fresh in demo mode so the ledger starts at 0 B, with cover traffic livelier for the camera: `DEMO=1 GV_COVER_INTERVAL_S=10 make demo`. For the phone beat use `bash phone/serve_https.sh` instead (C-015).
3. Pair the phone (Actions → **Use your phone**, type the 6-character code) and have the deck open on the red-team slide (7).
4. Screen layout: the app full-screen at 1080p, with the phone mirrored or filmed beside it. Turn off notifications.
5. Keep the on-screen note visible: "Demo, not medical advice. Synthetic data."

## The script

| Time | Beat | Narration | On screen |
| --- | --- | --- | --- |
| 0:00–0:15 | **S1 Hook** | "Alex just got a heart stent and five new prescriptions. One may not work for him, and two could hurt him. His genome and bloodwork could tell us, but would you upload your genome to a chatbot?" | Deck cover slide, then the app's Medications tab |
| 0:15–0:35 | **S2 Capture** | "He photographs the label. The photo is read on this laptop, not in the cloud, and isn’t kept." | Phone: tap **CLOPIDOGREL 75 MG** → “Is that right?” → **Yes, check it**. The laptop shows “From your phone · Clopidogrel 75 mg · 2 flags”. |
| 0:35–0:55 | **S3 Local flags** | "Four problems, found on the device: clopidogrel may barely work for his genes, omeprazole makes it worse, his statin dose, and his potassium. Zero bytes sent." | Medications tab: X1–X4 with severity. Point at the header: **0 B**, **0 personal fields**. |
| 0:55–1:30 | **S4 Hybrid** | "For an open question, it asks the cloud in disguise: general questions, each hidden in a fixed group of 8. Only this screen knows which one was real. And decoy groups go out even when Alex isn’t asking." | Ask tab → **What should I bring up with my cardiologist?** Its groups leave (8 blocks each): two on a fresh start, fewer if cover traffic already fetched one, since cover answers are stored too (B-009). Ask it within a few seconds of starting the app if you want two. Open one to show its 8 texts with “yours” marked. Point at a **Cover traffic** row. Read the “For you” paragraph. |
| 1:30–2:00 | **S5 Red team** | "We don’t claim privacy. We measure it. An attacker who sees everything that leaves finds the real question 100% of the time from a naive app, 99% with random decoys, and 11% with GenomeVault. Our smarter attacker gets 22%, and we report that number too." | Deck slide 7 (red-team chart) |
| 2:00–2:45 | **S6 Learns, offline, acts** | "Ask it again: answered on the device, zero bytes. Sync the knowledge pack, the same download for every user. Now offline, and it still answers. Pantoprazole instead of omeprazole? No data for that exact pair, so it doesn’t guess. And it drafts a message for his pharmacist." | Ask Q18 again (0-byte KB hit) → ledger panel **Sync knowledge pack** → header switch to **Offline** → ask a chip (0 B) → type **pantoprazole** → Medications tab: **ibuprofen** (four high flags) → Actions tab: pharmacist draft and visit summary |
| 2:45–3:00 | **S7 Close** | "Your genome never leaves your device. The cloud never learns what you asked. And the more you use it, the less it needs the cloud." | Deck slide 13 (vision) |

## If something goes wrong while recording

- **Q18 answers “no data”:** the knowledge pack isn't loaded. Stop, run `python -m core.cloud check`, and restart `make demo`.
- **The repeat question still sends groups:** the ledger was not fresh, or the pack isn't loaded; restart the app.
- **The phone won't connect:** skip the phone shot and type **Plavix** into “Check another medication” for S2.
- **Over time:** cut the cover-traffic line in S4 and the ibuprofen step in S6 first.
