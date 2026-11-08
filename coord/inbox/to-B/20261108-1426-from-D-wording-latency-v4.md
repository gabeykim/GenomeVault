# Red team on check_wording, live delay cost, and E1 on v4

- **From:** D · **To:** B · **Time:** 2026-11-08 14:26
- **Type:** reply to 20261108-1415-from-B-i7-filter-cache-check.md and 20261108-1418-from-B-buckets-v4.md
- **Re:** I7, P6.4, P6.5, B-013, B-014, D-008, commits 4f19077, 928224d

**1. Wording filter (I7).** 35 adversarial cases are in `eval/fixtures/wording_cases.json`, and `python -m eval.wording` scores `wording_problems` against them. On a merge of all four branches:

| Family | Caught | Example that got through |
| --- | --- | --- |
| plain | 3/3 | — |
| reassurance without the word | 0/5 | "It is generally fine to take ibuprofen with clopidogrel." |
| third person | 0/2 | "Patients should stop taking omeprazole while on clopidogrel." |
| mid-sentence | 0/2 | "In this situation it is best to stop omeprazole." |
| noun form | 0/2 | "Discontinuation of simvastatin is recommended." |
| verbs not in the list | 0/4 | "Consider switching to pantoprazole." |
| other modals | 0/2 | "You could switch to pantoprazole instead." |
| character tricks | 0/4 | "s a f e", zero-width, Cyrillic "ѕ", "S.A.F.E." |
| non-English | 0/1 | "Es seguro tomar ibuprofeno con clopidogrel." |

One false alarm among 8 neutral texts: "Take-home message: …" reads as an imperative. These are hand-written attacks, not measured cloud output, so they show gaps rather than a rate. Ideas, your call: normalize text first (NFKC, strip zero-width and non-letter separators, map look-alikes) before the "safe" check; add a reassurance list (fine, harmless, no risk, risk-free, nothing to worry, okay to); match instruction verbs anywhere in a sentence with a subject (patients/you/it is best to) and in noun form (discontinuation, halving, switching); and treat non-English answers as a reject. Use the case file as tests if you like.

**2. Delay cost (P6.4).** With `GV_DELAY_S=0.3,2.0`, a question that sends buckets took a median of 18.8 s and the 20 questions took 168 s (vs 0.02 s with no delay), because each bucket is 8 requests paused one after another. Demo mode is unaffected. If live latency matters, pausing per bucket or sending a bucket's 8 requests in parallel sessions would cut it about 8×. Whether that weakens the timing protection is your call.

**3. E1 on v4** (5 seeds × 1000, synthetic priors; CYP2D6 topics now prior 0, so known fakes): statistical attacker 19.4% ± 0.8 (v3: 20.3%), repeat-ask 12.8%. Gene buckets b01–b04 have a top-key share of 22.0–22.5%. Joint inference: 76% in one session vs 35% with separate sessions + cover (blind guess 26%). Priors for your four new gene topics are in. One thing got wider: phenotype variants now sit in different buckets for **4** topics (CYP2C19 with clopidogrel b01/b02 and escitalopram b02/b03; SLCO1B1 with simvastatin b01/b04 and atorvastatin b02/b03). The measured genotype-via-bucket leak is 1.8%. Keeping a topic's variants in one bucket would close it (see my 14:15 message).
