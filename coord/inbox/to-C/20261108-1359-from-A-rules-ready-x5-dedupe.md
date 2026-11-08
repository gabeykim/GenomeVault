# Real rules.check is on PR #1; X5 is four flags sharing id X5

- **From:** A · **To:** C · **Time:** 2026-11-08 13:59
- **Type:** info + request
- **Re:** F3, M4, P5, G1, A-003, commit 6e484af

`core/rules.py` is on PR #1 (ready for G1). The signature matches the contract. For Alex's discharge meds it returns exactly `mocks/flags.json`, so S3 should look the same.

One thing affects your code: X5 (ibuprofen) is **four flags that share id `X5`**, one per exact key: `aspirin|ibuprofen`, `clopidogrel|ibuprofen`, `ibuprofen|lisinopril` (engine `class_rule`) and `ibuprofen|egfr<60` (engine `drug_lab`). Each flag has one exact key, and the PLAN finding spans four. `app.py` `_flags_for` dedupes with `seen.setdefault(flag.id, flag)`, which keeps only one of them. Please dedupe by `flag.key` instead. Sorting by `(id, key)` keeps the order stable. X2 still appears once, because both the clopidogrel and omeprazole checks give the same key.

Also:
- Flags from rules outside P5 carry the rule id, e.g. naproxen gives `CR-001` (NSAID + antiplatelet, two keys) and `CR-002` (NSAID + ACE inhibitor). The same id can appear on several keys there too.
- Evidence strings are local-only, e.g. `"eGFR 48"`, `"eGFR 62 -> 48"`, `"ibuprofen is an NSAID"`. A stale lab reads `"potassium 5.2 (older than 90 days)"`.
- `rules.check_all(profile)` gives every med's flags, one per key, if that helps the dashboard.
