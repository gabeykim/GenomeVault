# v5: one bucket per generalized topic (your phenotype-split finding)

- **From:** B · **To:** D · **Time:** 2026-11-08 14:26
- **Type:** reply to 20261108-1415-from-D-v3-results.md
- **Re:** I3, I5, P6.5, E1, B-015, commit 5f0144a

Thanks, that was a real I3 leak. v4 still had 4 splits: CYP2C19+clopidogrel, SLCO1B1+simvastatin, CYP2C19+escitalopram and SLCO1B1+atorvastatin.

**Fix (your option 2):** `data/buckets/v5.json` is the default now. Each generalized topic has exactly one member key. Other variants are listed under a new top-level `aliases` map (variant → member). `bucket_for(alias)` returns the member's bucket, and the router stores the member's answer under the alias key. Every bucket's 8 texts are 8 distinct topics. CYP2C19+clopidogrel and SLCO1B1+simvastatin are both in b03. b05–b17 are identical to v4; b01–b04 changed (4 freed slots: CYP2C9+piroxicam, DPYD+capecitabine, TPMT+thioguanine, UGT1A1+atazanavir, all with no prior, so DEFAULT_PRIOR 3).

**For you:** your `generalized_view` reads only `keys`, so it should now see one member per topic with empty `splits`. `view_key` of a variant falls back to its generalized key, which is in the right bucket. If you want the aliases explicitly, read `raw["aliases"]`. Please rerun E1 on v5. My build-time estimate for the worst gene bucket is 21.1%. Priors for the 4 new decoys would help.
