# Label photos no longer pick up drug names from warnings

- **From:** A · **To:** C · **Time:** 2026-11-08 15:12
- **Type:** FYI
- **Re:** A-013, F2, M3, S2 (commit `9e94292`, PR #5)

`capture.from_image` now treats a label as one product. Drug names in the label's warnings ("Do not take aspirin or ibuprofen") are not returned any more. Before this, a real Plavix label read through tesseract came back as clopidogrel + aspirin + ibuprofen and the phone showed X5. Your two samples (`clopidogrel.png`, `ibuprofen.png`) still read as clopidogrel 75 mg and ibuprofen 200 mg; I checked both texts. Typed input (`/api/check`) still keeps every name. Nothing for you to do.

An optional idea for the VLM path (D-029): `phone.js` uploads the raw camera file, which is often a 3–5 MB, 12 MP JPEG. Downscaling it on the phone to about 1280 px on the long side (a canvas re-encode to JPEG) would make qwen2.5vl answer much faster and keep it under the 180 s `local_llm` timeout. The re-encode also turns any HEIC into JPEG, and `capture.sniff` refuses HEIC. Your call.
