# GenomeVault pitch outline (2 minutes without a demo slot, 3.5 with)

Numbers are from `docs/results.md`; re-run `make eval` on the integrated build at G4 and update the bracketed figures.
Current figures come from the simulated build and the stand-in bucket partition.

1. **Problem (20 s).** Whether a drug works for you, or hurts you, depends on your genes, your kidneys and liver, and your other medications. That data is scattered, and it is the most private data you have. Uploading it to a chatbot is a privacy and compliance problem.
2. **Insight (15 s).** Move the model to the data, not the data to the model. The AI PC holds the genome; the cloud only ever sees general, decoy-protected questions.
3. **What it does (45 s, or the live demo S2–S6).** Alex, 58, has just had a stent and has five new prescriptions. GenomeVault flags four problems on the device with 0 bytes sent. An open question goes out as fixed buckets of 8, and the answer comes back personalized locally. It works offline, and it drafts a message to his pharmacist.
4. **Proof, not promises (30 s).** "We don't claim privacy. We measure it."
   - Red team: naive leaks [100%], random decoys [95%] once a question repeats, fixed buckets [9%] (near 1 in 8). The statistical attacker reaches [17%], and we report that number too.
   - Joint inference: one session names the condition [60%] of the time; separate sessions plus cover bring it to [26%], about a blind guess ([19%]).
   - Learning: [6] cloud calls for 20 questions; [70%] answered on device; follow-ups are 0 bytes.
   - Offline: [10]/20 answered on a cold device, [18]/20 warm, and the rest get an honest "no data".
5. **Hybrid in Lenovo's terms (10 s).** What ran on the NPU/GPU (local model, rules, knowledge base) and what ran in the cloud (general reasoning over buckets), and why.
6. **Vision (10 s).** Personal device today; a clinic edge server next; federated queries across hospitals without moving a genome.

Charts for the slides: `docs/charts/redteam.svg` (S5), `docs/charts/joint.svg` (Q&A backup), `docs/charts/learning_curve.svg` (S7), `docs/charts/offline.svg` (S6).
On screen at all times: **Demo, not medical advice. Synthetic data.**
