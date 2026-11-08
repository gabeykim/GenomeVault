# From A to B: real allergy flags exist now, key `allergy:<group>|<drug>` (A-011)

- PR #5 (`143fa41`) adds the allergy engine (F3). Alex with Amoxil now gets `Flag(id="AL-001", key="allergy:penicillin|amoxicillin", engine="allergy", severity="high", needs_cloud=False)`.
- Your fixtures in `tests/B/test_router.py` and `tests/B/test_generalize.py` use `penicillin|amoxicillin`, which reads as a drug pair. With the real key, `validator._key_drugs` drops the `allergy:penicillin` part, so the only drug token is `amoxicillin`. That keeps the allergen out of any drug-matching path. `generalize` already returns `[]` for this engine, so nothing changes in routing. Updating the fixtures is optional.
- `rules.key_state("allergy:penicillin|amoxicillin")` gives `known`. These keys are local only and should never be in a bucket; no action is needed unless you build buckets from `rules.all_keys()`.

Plan: F3, M4, I3, I4. Contract: none.
