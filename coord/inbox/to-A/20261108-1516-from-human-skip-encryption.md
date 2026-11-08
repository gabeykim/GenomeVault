# Reply: skip encryption at rest (no `cryptography` dependency)

- **From:** human (Dhiaa) · **To:** A · **Time:** 2026-11-08 15:16
- **Type:** reply to 20261108-1454-from-A-crypto-dependency.md
- **Re:** AGENTS.md §9, BRIEF A stretch, I2, G3

Decision: **option 2, skip encryption at rest.** Do not add `cryptography` and do not change `core/graph.py` for it.

Why: it is a new dependency that every machine would need to install mid-integration (agents cannot pip install), it is not in any demo beat, and it touches `graph.py`, which everything reads from, right before G3. The pitch will say "stored locally; full-disk encryption via the OS (FileVault/BitLocker); app-level encryption with hardware-backed keys is on the roadmap." Please mark the stretch item as dropped in your STATUS.

Instead, for G3 (17:30): test `capture.from_image` against label images for Alex's five discharge meds plus an amoxicillin label (penicillin-allergy beat), and confirm each returns the right Drug, or no Drug for an unknown name, so C's confirm/edit step gets clean input. Report results in your LOG.
