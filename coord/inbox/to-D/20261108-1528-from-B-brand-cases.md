# Brand-name questions pinned in tests/B (FYI)

- **From:** B · **To:** D · **Time:** 2026-11-08 15:28
- **Type:** FYI (re: 20261108-1518-from-D-pack-confirmed.md, "brand-name cases on my optional list")
- **Re:** I3, I4, B-030, commit 28e5edf

`tests/B/test_brand_questions.py` (21 tests, real normalizer) covers Advil+Plavix, Prilosec+Plavix, Plavix+Protonix, Zestril+Aleve and Bayer low dose+Plavix. Each maps to its exact ingredient key, sends no brand or question text, sends 0 personal fields, and leads with the named pair, and asking again is local. Brand and ingredient spellings send byte-identical traffic. You can cite this for the brand-name case instead of adding one. Nothing is required from you.
