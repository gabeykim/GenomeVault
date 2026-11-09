# Stage script follows D-043; one false line fixed (pantoprazole)

- **From:** D · **To:** human (Dhiaa, Gabe) · **Time:** 2026-11-08
- **Type:** heads-up
- **Re:** D-043, D-020, PR #21 (`bfa1adc`), deck v18

`slides/presentation_script.md` is the word-for-word stage script (team intro → demo → close, about 4:45). It assumes D-043's switches are ON. On main plus #18–#20, #22 and #23 with them on, `demo_proof.py` gave 28 pass, 0 fail, 1 skip (live long-tail, needs your key).

- **S4** reads the new lead line, "Four things to raise with your cardiologist".
- **New 20 s step:** type "is asprin ok with my plavix" (assumed and shown), then "is clopidogral ok with my omeprazole" (asks first).
- **Fixed:** "pantoprazole instead of omeprazole → no data" was no longer true once the pack syncs; it answers from its own entry. "Never guesses" now uses "Does pantoprazole interact with my lisinopril?" → "GenomeVault has no data on pantoprazole with lisinopril." The demo script, video script and slide 10 match.
- If the proof turns everything off on the day, the script says what to skip.

Please merge PR #21 in D-043's order.
