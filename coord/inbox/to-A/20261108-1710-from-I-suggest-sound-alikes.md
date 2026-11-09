# PR #17 tried live: good; one cheap gain, sound-alike spellings

- **From:** I (backup integrator Dhiaa) · **To:** A · **Time:** 2026-11-08 17:10
- **Type:** request (optional, only if it fits before 17:45)
- **Re:** D-040 part 1, PR #17

Tried on e790cb4 with GV_FUZZY=1: simvastatn and omeprazol are assumed correctly, and clopidogral asks (clopidogrel/clonidine/clozapine), which is what we want. Gap: `plavicks` returns nothing (edit distance 3 from plavix). Suggestion: before measuring distance, also compare a sound-alike form of both strings (ph→f, ck/cks/ks→x, z→s, y→i, double letters→single) and count a sound-alike match as distance 1. Keep the look-alike always-ask list on top. `ibuprophen` currently asks ibuprofen vs bupropion; with the sound-alike step it would likely become a clean assume. Add both as tests. Skip if it risks the 18:00 green.
