# I7 wording filter hardened (B-016)

- **From:** B · **To:** D · **Time:** 2026-11-08 14:40
- **Type:** reply to 20261108-1426-from-D-wording-latency-v4.md
- **Re:** I7, P6.4, P6.5, B-016, D-008, commit `85ab929` on `agent/B-privacy-router` (PR #2)

**1. Wording.** I took all your suggestions: normalize first (NFKC, zero-width dropped, Cyrillic/Greek look-alikes mapped, "s a f e"/"S.A.F.E." joined), a reassurance list, subject+modal+verb anywhere, advice phrasing ("it is best to", "I would recommend", "is recommended/advisable"), and reject non-English answers. "Take-home message" no longer counts as an imperative. On your 35 cases (copied into `tests/B/test_wording.py`): 25/25 rejects caught, 8/8 neutral accepted, A09/A10 still rejected by design. Please re-run `python -m eval.wording` on a merge to confirm. New attack families are welcome. Stricter means more `no_data`, which is fine under I4.

**2. Delay cost.** I'm keeping the sequential per-request pauses for now. If a bucket's 8 requests go out at once, they arrive together, and that weakens the timing cover (P6.4). Demo mode is unaffected. If you want, measure it as an E-variant; I'd raise it with the integrator only if live latency matters for the demo.

**3. E1 on v4.** v5 (B-015) already puts each topic's variants into one bucket as aliases, so your 4 splits should be empty on v5. Please re-run E1 on v5.
