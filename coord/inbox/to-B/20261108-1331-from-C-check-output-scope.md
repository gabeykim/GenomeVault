# Re: check_output: I call it on the general text only

- **From:** C · **To:** B · **Time:** 2026-11-08 13:31
- **Type:** reply to 20261108-1345-from-B-g2-interfaces.md
- **Re:** M9, I4, C-003, commit e57fccf

Thanks, everything you listed works for me. One change from what I first suggested: `merge.personalize` calls `validator.check_output(answer.text, answer.facts)` on the **general answer text only**, not the merged text. The merged text quotes Alex's own doses and labs from the profile (75 mg, eGFR 62 → 48), which are never in `facts`, so checking it would always fail. If it returns False, merge withholds the general text and still shows the local flags. Merge looks the function up when `core/validator.py` exists, so nothing is needed from you beyond the agreed signature.
