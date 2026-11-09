# FYI: adaptive features ON for the demo (D-043)

- **From:** I (Dhiaa) · **To:** B · **Time:** 2026-11-08 17:45
- **Type:** heads-up
- **Re:** D-043, D-040

The demo machine will run with `GV_FUZZY=1 GV_TAIL=1 GV_DEMO_LIVE_FALLBACK=1 GV_INTENT=1 GV_DIRECT=1`, gated on `scripts/demo_proof.py` (PR #23) passing there with the live long-tail check. Merge order for Gabe: #22 → #20 → #18 → #21 → #19 → #23. Demo-critical fixes only from now; please keep your tests passing with all five flags exported as well as unset.
