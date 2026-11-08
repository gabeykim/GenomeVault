# From A to D: allergy engine for an eval question (A-011)

- PR #5 (`143fa41`) adds allergy flags (F3). Alex + amoxicillin → `allergy:penicillin|amoxicillin`, high, local only (B's `generalize` sends nothing for allergy flags, I3).
- A question you could add: "I was given Amoxil, is that OK with my record?" Expected: a local allergy flag, zero bytes out, and no reassuring wording (I7).
- I4 negatives: `allergy:penicillin|cephalexin` and `allergy:sulfonamide_antibiotic|furosemide` are `no_data`. We never infer cross-reactivity.
- Still open from me: Q08, whether `aspirin|clopidogrel` should be `known` offline (expected note) or `no_data`.

Plan: F3, M11, I3, I4, I7. Contract: none.
