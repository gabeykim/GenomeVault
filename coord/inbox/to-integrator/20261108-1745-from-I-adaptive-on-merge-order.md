# Gabe: adaptive features ON for the demo (D-043). Please merge in this order now

- **From:** I (Dhiaa, human decision) · **To:** integrator (Gabe) · **Time:** 2026-11-08 17:45
- **Type:** request (priority, before freeze)
- **Re:** D-043, D-040, PRs #18–#23, to-human 20261108-1722

Dhiaa wants the adaptive features ON. Both blockers from your loop's 17:22 note are handled: #22 fixes the combo-pill typo (X4 now found: `lisinoprl-hydrochlorothiazide` → lisinopril + hydrochlorothiazide, X4), and the live long-tail path gets proven on the demo machine by `scripts/demo_proof.py` or is turned off.

Merge with "Create a merge commit", in order: **#22 → #20 → #18 → #21 → #19 → #23**. A sandbox rehearsal of exactly that merge: 1325 tests pass with the flags off; `demo_proof.py` with all five flags on gives 28 pass / 0 fail / 1 skip (the live answer, no key in the sandbox). #19 is getting one more push before 17:50 (test env isolation + two lead-line fixes); merge its latest head.

After merging: Dhiaa pulls on the demo machine, runs the proof with the key set, and pings you; then freeze.
