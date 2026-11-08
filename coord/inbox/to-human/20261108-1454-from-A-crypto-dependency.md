# Question: add `cryptography` for A's encryption-at-rest stretch?

- **From:** A · **To:** human (Gabe, integrator through G2 per D-024) · **Time:** 2026-11-08 14:54
- **Re:** AGENTS.md §9 (new external dependency), BRIEF A stretch, I2

A's queue 1–8 and the PharmCAT stretch are done (PR #5). The last stretch item, encrypting the local SQLite profile (`core/graph.py`), needs a real cipher. Python's stdlib has none, and I won't write my own.

Options:
1. Add `cryptography` to `requirements.txt` (integrator-owned). I'd encrypt the profile with AES-GCM (`cryptography`'s AESGCM), using a key from an env var or a local key file kept outside the repo. It stays local only, so I2 holds. The default demo path doesn't change.
2. Skip encryption at rest. The pitch then says "stored locally" and not "encrypted at rest".

Reply in `coord/inbox/to-A/`. Until then I'll leave the item alone and handle requests from B/C/D.
