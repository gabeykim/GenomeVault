# capture.from_image done; OCR engine is your call (A-006)

- **From:** A · **To:** integrator · **Time:** 2026-11-08 14:30
- **Type:** FYI + optional request
- **Re:** D-020, M3, S2, I2, I8, A-006

`core/capture.py` (`from_image`, D-020) is on PR #1. It uses only the stdlib, makes no network calls (I2), and adds nothing to `requirements.txt`.

- With no OCR engine installed, it reads only images that carry embedded label text (`capture.demo_png(...)`, or a PNG text chunk / JPEG comment `gv:label`). That is enough for S2 in demo mode (I8).
- Reading a **real camera photo** needs the system `tesseract` binary on PATH (`brew install tesseract`). It is used only if present, as a local subprocess with a timeout. If you want live photos on stage, please install it on the demo laptop. If not, nothing changes.
- Option, not requested: if you'd rather use the local model for OCR, `core/local_llm.generate` would need an `images` parameter (yours). `capture.py` would then call it instead of tesseract. Tell me if you go that way.

PR #1 now covers queue 1-6 (145 tests green).
