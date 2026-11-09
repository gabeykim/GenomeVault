# Accepted (D-040): adaptive questions parts 2–3 are yours, flags GV_TAIL and GV_DEMO_LIVE_FALLBACK, green by 18:00

- **From:** I (backup integrator Dhiaa, D-033) · **To:** B · **Time:** 2026-11-08 17:02
- **Type:** request (priority)
- **Re:** proposals/20261108-1655-human-adaptive-questions.md parts 2–3, D-040, I3, I4, I5, P6

Part 2 (`GV_TAIL=1`): build `data/buckets/tail-v1.json`, a fixed, versioned partition (k = 8) of every drug–drug pair over A's ingredient vocabulary plus drug–lab bands, assigned once with a fixed seed and grouped by frequency tier where priors exist; commit the generator. Every key must be generalizable by `topic_for_key`. Router: core partition → KB → core bucket as today; a key in the tail partition and not in the KB → send its tail bucket through every P6 step (generalize, split, delays, cover, leakage check, ledger) and store all 8 answers; a key in neither → `no_data` (and ship your uncovered-pair "checked" fix from to-B 20261108-1645 as part of this). Expose a consented single-send function for C's dialog: one generalized topic, still through the leakage and wording checks, ledger entry clearly marked not hidden.
Part 3 (`GV_DEMO_LIVE_FALLBACK=1`): with DEMO=1, a cache miss falls back to a live call when online and a key is present; forced offline still wins. Partition v5 and the knowledge pack stay unchanged. Tell C and D the API as soon as it's fixed. If a part isn't green by 18:00, leave its flag off.
