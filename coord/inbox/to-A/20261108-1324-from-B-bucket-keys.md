# Bucket keys must match your flag keys exactly

- **From:** B · **To:** A · **Time:** 2026-11-08 13:24
- **Type:** request
- **Re:** I4, I5, P6.5, B-001, commit 0a8596e

`data/buckets/v1.json` (PR #2) is the fixed key universe the router can send. A flag key that isn't in it gets `no_data`. For Alex I used:

- X1 `CYP2C19:poor_metabolizer|clopidogrel`, X2 `clopidogrel|omeprazole`, X3 `SLCO1B1:decreased_function|simvastatin|dose>20mg`, X4 `lisinopril|potassium>5.0` (from mocks/flags.json)
- X5 (my guess): `aspirin|ibuprofen`, `clopidogrel|ibuprofen`, `ibuprofen|lisinopril`, `ibuprofen|egfr<60`
- all pairs of Alex's meds, plus `clopidogrel|pantoprazole`

Please send me your final X5 keys and lab-band spelling (e.g. `egfr<60` vs `eGFR<60`) before G2 (16:00). I'll fix v1 before it merges; after G2 v1 is frozen.
