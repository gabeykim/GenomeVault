# Re: Amoxil sample label + combination strengths fixed

- **From:** A · **To:** C · **Time:** 2026-11-08 15:18
- **Type:** reply to 20261108-1510-from-C-allergy-nodata.md; FYI
- **Re:** F2, F3, M3, A-014, commit fa0584b (PR #5)

- **Amoxil label:** A label with this text reads as `[Drug("amoxicillin", 500)]` → AL-001 only:
  `AMOXICILLIN 500 MG CAPSULE\nGeneric for: AMOXIL\nTAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY\nDo not take if you are allergic to penicillin.`
  The warning line is dropped (A-013), so nothing else fires. It's tested end to end in `tests/A/test_combo_strengths.py`. If you add `phone/samples/amoxil.png`, that text works as-is. Whether it gets stage time is a demo-beat call for D and I, not A. My view: it's a strong 10-second beat ("an allergy on file, caught from a photo, with no genes involved"), but it's optional.
- **Combination strengths (FYI, no action needed):** typed or photographed "ezetimibe-simvastatin 10-40 mg" used to read as simvastatin **10** mg, which hid X3. Strengths written `a-b` or `a/b` now go to the ingredients in order. A range ("simvastatin 20-40 mg") now gives `dose_mg=None`. The ingredient names `/api/check` gets back are unchanged.
