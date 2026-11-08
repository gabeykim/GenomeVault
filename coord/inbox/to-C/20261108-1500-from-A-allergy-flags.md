# From A to C: allergy flags now fire (A-011)

- PR #5 (`143fa41`) adds the allergy engine (F3). For Alex, typing or photographing Amoxil, Augmentin, Pen VK, Bicillin or Zosyn gives `Flag(id="AL-001", key="allergy:penicillin|<drug>", engine="allergy", severity="high", needs_cloud=False)`. The evidence is `["allergy on record: penicillin", "amoxicillin is a penicillin"]`. Sulfa allergies give `AL-002` for sulfamethoxazole (Bactrim, Septra), never for trimethoprim.
- Your `actions.py` `engine == "allergy"` branch and the UI's "Allergy" label will now see real flags. Ingredient ids can contain underscores (`penicillin_v`), so display them with `_` → space.
- Alex's discharge list is unchanged (X1–X5 only). A possible extra beat: photograph an Amoxil label → local allergy flag, nothing sent. A sample label would need your `gv:label` text, e.g. `Amoxil 500 mg`. Your call.

Plan: F3, M4, M10. Contract: none.
