# Please confirm two lab-band spellings in bucket v2

- **From:** B · **To:** A · **Time:** 2026-11-08 14:10
- **Type:** question (reply before G2 if possible; v2 freezes at G2)
- **Re:** B-011, commit f545cff, P6.5, P5

Bucket partition v2 adds keys for D's questions: `lisinopril|egfr<60`, `simvastatin|alt>120`, `CYP2C19:poor_metabolizer|citalopram`. Other new keys: `apixaban|egfr<30`, `acetaminophen|alt>120`, `lithium|egfr<60`, `atorvastatin|alt>120`, `valproate|alt>120`, `methotrexate|egfr<60`, `CYP2C19:poor_metabolizer|sertraline`, `CYP2C19:poor_metabolizer|omeprazole`, `SLCO1B1:decreased_function|atorvastatin`, `HLA-B:5801_positive|allopurinol`, `HLA-B:1502_positive|carbamazepine`, `CYP2D6:poor_metabolizer|tamoxifen`, `CYP2C9:poor_metabolizer|phenytoin`. If your rules emit any of these with different spelling or bands (e.g. ALT as `alt>3xULN`), tell me and I'll match yours.
