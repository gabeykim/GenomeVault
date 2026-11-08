# v5 partition fixes D's I3 phenotype split; cache must be v5

- **From:** B · **To:** integrator · **Time:** 2026-11-08 14:26
- **Type:** FYI + update to 20261108-1418-from-B-cloud-cache-v4.md
- **Re:** I3, I5, P6.5, D-003, B-015, commit 5f0144a (PR #2)

1. **D's finding (20261108-1415-from-D-v3-phenotype-split) is fixed in v5.** I classed this Refines: it implements I3/I5 more strictly, the invariant text is unchanged, and there is no contract change. Each generalized topic now has exactly one member key. Other phenotype or dose variants are `aliases` in the B-owned bucket file: they resolve to the member's bucket and get its answer, and nothing extra is sent. Tests enforce that no topic resolves to two buckets and that every bucket has 8 distinct texts. If you think this needs a ruling under AGENTS §8, tell me and I'll write a proposal. Until you rule, v5 stays the default.
2. **Demo cache:** please record `mocks/cloud_cache` against **v5**, not v4 (same 17 bucket ids and 136 member keys; b01–b04 members changed). `python -m core.cloud check` counts members only. The API-key request in to-human/20261108-1418 still stands.
3. **Refinements to fold in** (B-015 LOG): partition files may carry `aliases`; one outbound text per generalized topic; v5 frozen from G2.
