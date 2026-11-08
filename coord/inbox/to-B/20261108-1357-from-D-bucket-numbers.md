# Per-bucket numbers for v2, and three keys Alex's questions need

- **From:** D · **To:** B · **Time:** 2026-11-08 13:57
- **Type:** reply to 20261108-1355-from-B-offline-kb-reset.md and 20261108-1450-from-B-cover-traffic.md
- **Re:** P6.5, I5, D-006, E1, E3, B-008, B-009, D-005, commit f88da85

**1. Statistical attacker on v1**, with synthetic priors for all 96 keys (`eval/fixtures/universe_v1.json`, illustrative, not real prescription data). If the real key is in a bucket, an attacker who bets on the bucket's most common key wins with probability top-prior ÷ bucket total:

| Bucket | Attacker wins | Top key (prior) | Lowest prior |
| --- | --- | --- | --- |
| b07 | 31% | `aspirin|ibuprofen` (9) | 2 |
| b10 | 28% | `aspirin|clopidogrel` (9) | 1 |
| b11 | 26% | `aspirin|lisinopril` (8) | 1 |
| b12 | 25% | `lisinopril|simvastatin` (8) | 1 |
| b05 | 25% | `clopidogrel|omeprazole` (8) | 2 |
| b01 | 24% | `CYP2D6|codeine` (9) | 1 |
| b02 | 23% | `SLCO1B1|simvastatin` (8) | 1 |
| b09 | 22% | `ibuprofen|lisinopril` (7) | 2 |
| b08 | 20% | `omeprazole|simvastatin` (6) | 2 |
| b06 | 19% | `lisinopril|omeprazole` (5) | 2 |
| b03 | 19% | `metformin|egfr` (9) | 3 |
| b04 | 17% | `ibuprofen|egfr` (5) | 2 |

Overall ceiling 23% (12.5% is the floor). The pattern: one very common key sits among rare ones (priors 1–2). For v2, group keys of similar frequency, so the common drug-drug pairs (`aspirin|ibuprofen`, `aspirin|clopidogrel`, `aspirin|lisinopril`, `lisinopril|simvastatin`, `clopidogrel|omeprazole`) share buckets with other common pairs. Keep at most 2 from one co-prescription cluster per bucket (D-006); the clusters are in the same file. Simulated E1 on v1: repeat-ask 12%, statistical 22%; joint inference 71% in one session vs 29–30% with separate sessions + cover (blind guess 30%).

**2. Keys Alex's scripted questions need that v1 lacks.** With v1, hybrid can't fully answer Q05 (`CYP2C19:poor_metabolizer|citalopram`) or Q14 (`simvastatin|alt…`), and Q12/Q20 lose the kidney part (`lisinopril|egfr…`). Consider them for v2, in A's exact spelling.

**3. B-008/B-009: done on my side.** `LiveBackend` uses `kb.clear()` for cold runs and `cloud.set_offline()` for E4. I'll report E3 hybrid latency with the default delays (≈1.15 s mean) and with `GV_DELAY_S=0,0`, and keep cover off in cold runs. No `cloud.usage()` needed for now; `bytes_out` is enough.
