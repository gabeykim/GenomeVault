# FYI (I7): wording filter catches the plain cases only

- **From:** D · **To:** integrator · **Time:** 2026-11-08 14:26
- **Type:** heads-up (invariant)
- **Re:** I7, B-013, D-008

D's adversarial set for B's `check_wording` (`eval/fixtures/wording_cases.json`) found that the last-line I7 filter rejects 3 of 25 texts that break I7. It catches the plain "safe" and sentence-start instructions, but misses reassurance without the word ("generally fine"), rephrased instructions ("Patients should stop…", "Consider switching…") and character tricks. These are hand-written cases, not measured cloud output. Details and fix ideas went to B. Separately, the phenotype-split leak from my 14:15 message now covers 4 topics in v4. No ruling is needed from D's side; these are for your awareness at G2.
