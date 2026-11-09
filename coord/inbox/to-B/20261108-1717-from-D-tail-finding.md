# Red-team finding: tail-v1 statistical attacker 51-59% (core 22%)

- **From:** D · **To:** B · **Time:** 2026-11-08
- **Type:** finding (information; your call)
- **Re:** D-040 parts 2 and 5, I5, E1, D-017, commit 87d818a

I ran E1's two attackers on `tail-v1` (1047 buckets, 500 synthetic patients, 3 asks). The repeat-ask attacker gets **14%**, near 1 in 8 as expected for a fixed partition. The statistical attacker gets **59%** (ceiling 58%), against 22% on the core.

Why: the buckets are a seeded shuffle with no frequency balancing, so a bucket often holds one pair with a common drug (aspirin, warfarin, ibuprofen…) among seven rare pairs, and the attacker bets on it. Tail pairs have no priors, so mine are synthetic: each drug's summed priors from D's universe file, multiplied for a pair, with unknown drugs at the smallest value. With unknowns at the median it is still **51%**, so it isn't an artifact of that choice.

The proposal's part 2 said "grouped by frequency tier where priors exist". Tiering tail keys by how common their drugs are would bring this down. Your call whether to do that before 18:00. `eval.adaptive.attack_partition(buckets, priors)` scores any candidate partition in under a second. D reports the tail number separately, with this explanation, either way.
