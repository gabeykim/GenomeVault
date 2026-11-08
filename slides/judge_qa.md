# Judge Q&A

Name the weakness before they do, then show the measurement or the fix. Figures come from `docs/results.md`.

| Question | Answer | Evidence |
| --- | --- | --- |
| Doesn't the cloud still learn your genotype? | No. Questions cover every phenotype and lab band, and the right section is picked on the device. Genotype, age and lab values leaked in 0% of generalized transcripts. | E1 table, "Genotype leaked" column |
| Couldn't repeat questions reveal you? | Not with fixed buckets: a topic always sends the same 8. Random decoys fail exactly here (about 95% recovered after 3 asks); we show both. | `redteam.svg` |
| Is 1 in 8 really what you get? | Against a uniform guesser, yes. A smarter attacker who bets on the most common topic gets about 17% on our current partition. We report that number, and B's bucket design targets equal frequencies inside each bucket. | E1 statistical attacker, bucket design report |
| A discharge sends several buckets at once. Can they be combined? | In one session, yes: the attacker names the condition about 3x more often than a blind guess. That's why buckets go in separate sessions with cover traffic, which brings it near a blind guess. | `joint.svg`, D-006 |
| What about IP address and timing? | Out of scope today; linkable sessions still give an attacker a small edge, and we measure it. The roadmap fix is a relay layer. | Joint table, "linkable" row |
| Why use the cloud at all? | Rules cover guideline lookups. The cloud handles open-ended reasoning, its answers are stored, and use falls over time (6 calls for 20 questions). | `learning_curve.svg` |
| Why not download every answer? | For the finite guideline set that is the endpoint, and bulk sync is on the roadmap. Decoys protect open-ended questions. | README roadmap |
| What if the cloud answer is wrong? | Trust tiers: serious warnings need a curated source; cloud facts are labeled "AI-summarized, verify" and expire sooner. | I6 |
| Does it guess between similar drugs? | Never. Facts are keyed to exact ingredients; pantoprazole does not borrow omeprazole's answer. | Q07, I4 |
| Isn't this medical advice? | It prepares you for your pharmacist or doctor and never says start or stop. Demo data is synthetic. | I7, I1 |
| Are your numbers real or simulated? | Today's charts come from a simulation of the privacy stack and a stand-in partition; `make eval` re-runs them on the integrated build, and the results page states which build produced them. | `docs/results.md` status line |
| Why is this an agent, not a chatbot? | It watches new inputs, re-checks meds when labs change, drafts messages and sets reminders across devices. | Demo S6 |
