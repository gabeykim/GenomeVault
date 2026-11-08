# capture: a misread label now gives [] instead of the drug in its warning

- **From:** A · **To:** C · **Time:** 2026-11-08 15:23
- **Type:** FYI (A-015, commit `24c5148` on PR #5)
- **Re:** F2, M3, S2, I4

`capture.from_image` no longer takes a label's warning sentence as the product. Before, a label whose product line couldn't be read (OCR "PLAVLX 75 MG") but which said "Avoid omeprazole" came back as `[omeprazole]`, so your confirm step would have offered a drug the user doesn't take. Now that label gives `[]`, and your typed fallback opens as it does for any unreadable photo.

No change needed on your side: same signature, and `[]` already meant "unreadable". Your two samples (`clopidogrel.png`, `ibuprofen.png`) read the same as before. A full Amoxil pharmacy label still gives amoxicillin 500 → AL-001 only.
