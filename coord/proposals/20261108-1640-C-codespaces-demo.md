# Proposal: one-click GitHub Codespaces demo link (repo config)

- **From:** C · **Time:** 2026-11-08 16:40 · **Against:** PLAN v1.3.3
- **Type:** scope change (repo config only; no PLAN behavior, contract or invariant change)
- **Problem:** Cristian wants a GitHub link that runs the demo just like it runs locally. Today you have to clone the repo, install and run `make demo`. Judges and teammates without a setup can't try it.
- **Proposed change:** PR #13 (branch `integrator/codespaces-demo`, prepared by C, tagged [I] for your review) adds `.devcontainer/devcontainer.json`. It uses Python 3.11, installs `requirements.txt`, and runs `DEMO=1 python -m uvicorn app:app --host 0.0.0.0 --port 8000` with port 8000 opened in the browser. It also adds a "Try the demo" section to `README.md` with the badge and link `https://codespaces.new/gabeykim/GenomeVault?quickstart=1`. C's own part is `82a7205` on PR #11: in a codespace, Actions → Use your phone shows the forwarded HTTPS address.
- **Affects:** I: review and merge PR #13; optionally set About → Website to the link (admin only). D: the link can go in `docs/submission.md` and the slides. A, B: none. Demo mode replays `mocks/cloud_cache`, nothing calls the cloud (I2, I8), and the data is synthetic (I1).
- **Migration:** none.
- **If rejected:** close PR #13. The local `make demo` and `phone/serve_https.sh` are unchanged, and C's `82a7205` does nothing outside a codespace.

Checked: a clean install from `requirements.txt` with the container's start command and Codespaces environment variables, on main + PR #11. `/` and `/phone` return 200, all modules are real, flags are X1–X4, Q18 is `known`, Sync stored 122 facts, 0 personal fields. A real codespace boot is still to check after merge.

---
_Integrator ruling (integrator fills in via DECISIONS.md, not here)._
