# Presentation script, word for word, start to finish (live demo)

The stage run: team intro, slides and the live demo, about 4:45, then questions. Words in quotes are spoken. *Italics* are actions. **[Slide N]** is on the projector; **[App]** means the laptop screen.

It matches the build as of PLAN v1.3.7 (D-043): typo-tolerant and paraphrased questions, answer-first lead lines and long-tail lookups are **on** for the demo. Every app line below was run through the merged build with those switches on (`scripts/demo_proof.py`: 28 pass, 0 fail, 1 skip for the live long-tail answer, which needs the demo machine's key). Every figure comes from G4 (`slides/numbers.md`).

The lines are written for Kaitlyn as the main speaker. If someone else opens, they swap in their own "I'm…" line.

## Before you go on stage (5 minutes earlier)

- On the demo machine, start the app with the D-043 switches and label reading on: `GV_FUZZY=1 GV_TAIL=1 GV_DEMO_LIVE_FALLBACK=1 GV_INTENT=1 GV_DIRECT=1 DEMO=1 GV_OCR=vlm bash phone/serve_https.sh`. Pair the phone (Actions → **Use your phone**, type the 6-character code).
- `scripts/demo_proof.py` must have exited 0 on this machine. If its live long-tail check failed, `GV_TAIL` and `GV_DEMO_LIVE_FALLBACK` are off (D-043). Nothing in the main run below needs them.
- **Sync the knowledge pack now**, off stage, and wait until it finishes. On stage you only mention it.
- Scroll once past the full-screen GenomeVault title so the app sits on the **Medications** tab.
- Deck open on slide 1. Have the backup video ready to play.
- Decide who holds the phone and who clicks the laptop.
- Never say "safe", "no interaction", or "you should stop/start". Say "no interaction listed", "worth asking your pharmacist".

---

## 0:00 · [Slide 1 · Cover] · Team intro · 25 s

*Walk up together. The speaker stands at the laptop; the others stand beside the screen.*

"Hi, we're GenomeVault. I'm Kaitlyn. I built our evaluation and red team: the part that attacks our own system to prove it's private."

*Gesture to each teammate as you name them.*

"Gabe built the patient data and the medication rules. Dhiaa built the privacy layer and pulled all four parts together. And Cristian built the app and the phone. We built this today with four AI coding agents working side by side, one supervised by each of us."

**Hand-off version** (each person says their own line instead, about the same length):
- Kaitlyn: "I'm Kaitlyn. I built the evaluation and red team, the part that attacks our own system."
- Gabe: "I'm Gabe. I built the patient data and the medication rules."
- Dhiaa: "I'm Dhiaa. I built the privacy layer and put the pieces together."
- Cristian: "I'm Cristian. I built the app and the phone."
- Kaitlyn: "Four AI coding agents built it in parallel today, one supervised by each of us."

## 0:25 · [Slide 1 · Cover] · The hook · 20 s

"Here's why. Alex is 58. He just got a heart stent and went home with five new prescriptions. One of them may barely work for him, and two others could hurt him. His genome and his bloodwork could tell us which. But would you upload your genome to a chatbot? We built GenomeVault so you never have to."

*Advance.*

## 0:45 · [Slide 2 · Three private things] · 20 s

"Whether a drug is right for you depends on three private things: your genes, how your body is doing right now, and your other medications. For Alex, his genes mean clopidogrel may barely activate. His kidney function is falling. And omeprazole makes the clopidogrel problem worse. That's the most private data you have."

*Advance.*

## 1:05 · [Slide 3 · The idea] · 10 s

"So we flipped it. Move the model to the data, not the data to the model. The AI PC holds the genome. The cloud only ever sees general questions, hidden among decoys."

*Advance.*

## 1:15 · [Slide 4 · Everything personal stays on the AI PC] · 15 s

"Everything personal, his genes, meds and labs, lives on this laptop. A rules engine checks every drug right here. When we do need the cloud, a privacy router sends only general questions, eight at a time, and a ledger records every byte that leaves. Let me show you."

*Switch to the app (Medications tab). Whoever holds the phone steps forward.*

## 1:30 · [App · phone] · Capture · 25 s

"Alex photographs a new prescription on his phone."

*On the phone, tap the **CLOPIDOGREL 75 MG** sample label. "Reading the label on this laptop…" shows for about 4 seconds.*

"A vision model on this laptop reads it. About four seconds, no cloud, and the photo isn't kept."

*The phone asks "Is that right?" Tap **Yes, check it**. Two red flags appear.*

"It asks him to confirm, and it's already flagged twice."

## 1:55 · [App · Medications tab] · Local flags · 20 s

*Point at the four flags, then at the ledger header.*

"Here's everything he takes. Four problems, found on the device: clopidogrel may barely work for his genes, omeprazole makes that worse, his statin dose carries a muscle risk, and lisinopril with his potassium and kidneys. And up here: zero bytes sent, zero personal fields."

## 2:15 · [App · Ask tab] · The cloud in disguise · 40 s

*Click the **Ask** tab, then the chip **What should I bring up with my cardiologist?***

"Now an open question that needs real reasoning: what should he bring up with his cardiologist?"

*Point at the strand as blocks slide across, then at the ledger.*

"Watch the ledger. Each question leaves inside a group of eight look-alike questions. Those are the blocks."

*Click **See the 8 questions**.*

"Eight general questions. Nothing about Alex. Only this screen knows which one was his. Zero personal fields."

*Point at the **Background decoys** line.*

"And this line is decoy traffic. It goes out even when Alex isn't asking."

*Point at the answer's first line, "Four things to raise with your cardiologist:".*

"The answer comes back general and is personalized here on the laptop: four things to raise with his cardiologist, each tied to his own results."

## 2:55 · [App · Ask tab] · Ask it your own way · 20 s

*Click in the question box and type **is asprin ok with my plavix**, misspelled, then press Enter.*

"Real people don't type like our script. Misspelled, brand name, casual."

*Point at "I'm assuming you mean aspirin." and "I took this as: Does aspirin interact with clopidogrel?"*

"It works out what he meant, on the device, and shows its assumption. He can undo it."

*Clear the box, type **is clopidogral ok with my omeprazole**, press Enter.*

"But a name that looks like another drug, it won't assume. It stops and asks: clopidogrel, clonidine or clozapine? Nothing is checked or sent until he picks."

*Switch to the deck, slide 7.*

## 3:15 · [Slide 7 · We don't claim privacy. We measure it.] · 25 s

"We don't claim privacy. We measure it. That's my part: we gave everything that left the laptop to an attacker, across 500 synthetic patients."

*Point down the chart, top to bottom.*

"A naive app gives the question away every time. Random decoys look fine once, but ask three times and only the real question survives: 99%. Our fixed groups of eight: 11%, right at this line, one in eight, the best a group of eight can do. A smarter attacker that bets on common drugs gets 22%, and we report that number too."

*Advance.*

## 3:40 · [Slide 9 · Same 20 questions, two ways to ask] · 10 s

"Same 20 questions, two ways. A cloud-only app sends 420 personal fields. GenomeVault sends zero, with only 11 cloud calls."

*Switch to the app (Ask tab).*

## 3:50 · [App · Ask tab] · Learns, offline, never guesses, acts · 35 s

*Click the cardiologist chip again.*

"It learns. Same question again: answered on the device, zero bytes. We also synced the knowledge pack, which is the same download for every user, so it reveals nothing."

*Click the **Online** switch so it reads **Offline**. Click the chip **Could pantoprazole work instead of omeprazole with my clopidogrel?***

"Now there's no network, and it's still answering. Pantoprazole instead of omeprazole: it answers that exact pair from its own entry, listed as minor, and marked 'AI-summarized, verify'. It doesn't borrow omeprazole's answer."

*Type **Does pantoprazole interact with my lisinopril?**, press Enter.*

"And a pair it has nothing on? 'GenomeVault has no data on pantoprazole with lisinopril.' It never guesses."

*Click the **Actions** tab.*

"And it acts: a message drafted for his pharmacist, and a one-page visit summary."

*Click **Offline** back to **Online**. Switch to the deck, slide 13.*

## 4:25 · [Slide 13 · Where it goes] · Close · 20 s

"Today this runs on your AI PC. Next, a clinic or pharmacy server running the same stack. Then, questions across hospitals without moving a single genome. Your genome never leaves your device, the cloud never learns what you asked, and the more you use it, the less it needs the cloud."

"We're Gabe, Dhiaa, Cristian and Kaitlyn, and this is GenomeVault. Thank you."

## 4:45 · Questions, and let the judges type

*Leave slide 13 up. Bring the laptop to the Ask tab.*

"We'd love your questions, and you're welcome to type your own into the app. Gabe can take the medication rules, Dhiaa the privacy layer, Cristian the app, and I'll take how we tested it."

**Running long?** Cut in this order: the hand-off intro (use the single-speaker one); slide 9 (fold "420 versus zero" into slide 7's last line); the decoy-traffic sentence at 2:15; the look-alike half of "Ask it your own way"; the Actions tab. Each saves 5–15 seconds.

**If D-043's switches are all off** on the day (the proof failed outright): skip "Ask it your own way", and at 2:15 read the first sentence of the "For you" paragraph instead of "Four things to raise". Everything else is unchanged.

---

## When a judge types a question

| They type | What happens | Say |
| --- | --- | --- |
| A paraphrase or typo of a scripted question | "I took this as: …", then the answer | "It maps what you typed to a question it already answers, on the device, and tells you what it took it as." |
| A rare drug pair (e.g. amoxicillin with warfarin), online | Ledger: "Tail group of 8 sent". With the demo machine's key, a live answer | "Rare pairs are hidden too, in their own fixed groups of eight." |
| The same rare pair, offline or with no key | "GenomeVault has no data on … with …" | "It doesn't have that pair stored, so it says so. No guess." |
| "Can I take X for a headache?" / "Should I stop…?" | "GenomeVault does not answer whether to take X; that is a question for your pharmacist or doctor. What it found: …" | "It never tells you to start or stop anything. It shows what it found, and sends you to your pharmacist." |
| A look-alike name (clopidogral, lamictl…) | "Did you mean: …?", nothing sent | "It asks instead of guessing when names look alike." |

## Held for questions

| If they ask | Who answers | Show | Say |
| --- | --- | --- | --- |
| "Can several questions together reveal him?" | Kaitlyn | Slide 8 | "Sent in one session, an attacker names the condition 72% of the time. In separate sessions with decoys it's 34%, against a 26% blind guess." |
| "How do you know it's private?" | Kaitlyn | Slide 11 | "Our red team attacks our own build. Today it found real problems, like a wording filter that caught 3 of 25 rephrased advice texts, and the team fixed each one. Now it catches 25 of 25." |
| "What about the typo fixing? Could it pick the wrong drug?" | Kaitlyn | — | "We tested it with our own 20 misspellings, including look-alike names. It found the right drug 20 times out of 20 and never silently swapped in a wrong one. Look-alikes always ask." |
| "Are rare pairs as private as common ones?" | Kaitlyn | — | "We measure them separately. Our first rare-pair groups let a smart attacker win 59% of the time, because one common drug stood out. Dhiaa regrouped them by how common each drug is, and that dropped to 15%." *(Only if B's PR #20 is merged; otherwise: "We measure them separately, and we found and fixed a weakness in how they were grouped today.")* |
| "What doesn't it do?" | Dhiaa | Slide 12 | "It doesn't hide IP address and timing yet; a relay layer is the fix. Privacy is 1 in 8, not zero. And it never tells you to start or stop a medication." |
| "Where do the medication rules come from?" | Gabe | Slide 5 | "Fixed, guideline-style lookup tables for genes, drugs, labs and allergies, not an AI guessing. They cover Alex's drugs and their neighbors today. The data is synthetic." |
| "What runs on the laptop, and what in the cloud?" | Dhiaa | Slide 4 | "On the laptop: his records, the rules, the knowledge base, the personalization, the typo and question understanding, and a vision model that reads labels. In the cloud: only general questions, eight at a time." |
| "Does the phone keep anything?" | Cristian | — | "No. The photo goes to the laptop to be read and isn't kept. The phone shows the result and gets reminders that say only 'Call your pharmacist.'" |
| "Is it slow?" | Dhiaa | — | "Most questions are answered instantly on the device. A question that does go out waits on purpose, with random pauses that hide when you're active. On stage we replay the recorded answers." |

More answers are in `slides/judge_qa.md`.

## If the demo breaks

- **Phone won't connect:** "Let me type it instead." Type **Plavix** into "Check another medication" and carry on from the Medications step.
- **An answer reads "no data" at 2:15:** "This is the recorded pack not loading. Here's the run we recorded." Play the backup video from 0:55.
- **Anything else:** "Let me show you the recording." Play the backup video from the step you were on, and keep talking over it with the same words.
