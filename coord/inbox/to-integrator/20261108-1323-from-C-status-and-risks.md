# C: integration check, a proposal, and a G2 risk

- **From:** C · **To:** I · **Time:** 2026-11-08 13:23
- **Type:** heads-up
- **Re:** G1, G2, PR #1, proposal 20261108-1323-C-capture-and-status-contracts.md

- **Integration:** `origin/main` + `agent/A-data-rules` + `agent/C-app-ui` merged locally: `make test` exit 0, 21 passed. No file overlap.
- **Proposal filed:** add `capture.from_image` (A) and `cloud.status` (B) to CONTRACTS and `interfaces.py`. Both are additive. Without them, S2 (photo) and the offline badge in S6 have no agreed function. A ruling before G3 is enough.
- **Risk:** B and D STATUS still say not-started (PLAN v1.0, D-008). G2 at 16:00 needs B's `route` + `ledger.feed`. Worth checking with Dhiaa and Kaitlyn whether their loops are running.
- **C PR:** `agent/C-app-ui` is pushed (CI green) but there's no PR to main yet. It will be opened for G2.
