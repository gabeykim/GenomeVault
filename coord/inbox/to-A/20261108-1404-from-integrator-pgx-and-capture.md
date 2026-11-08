# Integrator pass: PGx corrections + capture.from_image (D-020, D-021)

- **From:** integrator (Gabe, backup) · **To:** A · **Time:** 2026-11-08 14:04
- **Type:** ruling + task (Advances of PLAN v1.2)
- **Re:** P5, D-021, D-020, CONTRACTS, M3, M4, X5

PLAN is now **v1.2**. The items below are **Advances** (they implement what v1.2 now specifies). Add tests under `tests/A/`.

**PGx corrections (D-021):**
1. **CYP2D6 is `not_assessed`** — gene deletions/duplications are not callable from SNP data. No rule may read CYP2D6. Update the profile/genotype data and remove any rule path that used it.
2. **`aspirin|clopidogrel` is expected dual antiplatelet therapy after a coronary stent** — it must NOT produce a Flag. Add `data/rules/expected_combinations.json` listing expected combinations; the engine surfaces them as an informational note, not a flag. The NSAID + antiplatelet rule (**X5**) must still fire for `ibuprofen`.
3. **Match genotypes by rsID** (the VCF `ID` column), never by position. Fix VCF positions to **GRCh38** per dbSNP:
   - rs4244285 (CYP2C19\*2) → chr10:94781859
   - rs4986893 (CYP2C19\*3) → chr10:94780653
   - rs12248560 (CYP2C19\*17) → chr10:94761900

   Note: 94775489 is **rs17884712 / CYP2C19\*9**, NOT \*3. Any other position you cannot verify: mark it `position unverified; matched by rsID` in `data/README.md`.

**New contract (D-020):** implement `capture.from_image(data: bytes, mime: str) -> list[Drug]` (M3, queue 6): OCR + `normalize.to_ingredients` internally; return `[]` for unreadable images. A mock stub lives in `core/interfaces.py` until your real code merges (G3).

**Tests to add:** X1–X4 still fire for Alex's discharge meds; `aspirin+clopidogrel` produces **no** flag (informational only); `ibuprofen` still fires X5; genotype matching is by rsID.

This is the G1 blocker — please prioritize `rules.check` for X1–X4.
