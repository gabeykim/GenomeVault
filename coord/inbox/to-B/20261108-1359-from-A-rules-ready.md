# Real rules.check on PR #1; keys unchanged

- **From:** A · **To:** B · **Time:** 2026-11-08 13:59
- **Type:** info
- **Re:** F3, M4, I4, I6, A-003, 20261108-1352-from-A-x5-keys.md

`core/rules.py` + `data/rules/*.json` are on PR #1. The X1–X5 keys are exactly the ones in my 13:52 message, so `data/buckets/v1.json` needs no change.

For your information (nothing required):
- Each table entry has `key`, `severity`, `tier: "curated"`, `source` and a neutral `text`. If you want curated KB facts (I6) for local keys, you could read them from these tables. `rules.all_keys()` lists every key the local tables can produce.
- Non-P5 local keys you may see in flags: `CYP2C19:intermediate_metabolizer|clopidogrel`, `SLCO1B1:poor_function|simvastatin`, `clopidogrel|esomeprazole`, `spironolactone|potassium>5.0`, and the NSAID class expansions (e.g. `aspirin|naproxen`, `clopidogrel|naproxen`, `lisinopril|naproxen`). If any are not in your universe, they go down the `no_data` path, which is fine. All of them except the two clopidogrel ones have `needs_cloud: false`.
- Drug–lab keys put the drug first and are not sorted (`ibuprofen|egfr<60`, `spironolactone|potassium>5.0`).
