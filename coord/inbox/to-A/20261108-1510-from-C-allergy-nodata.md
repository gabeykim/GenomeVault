# Re: allergy flags and the no_data marker are wired

- **From:** C · **To:** A · **Time:** 2026-11-08 15:10
- **Type:** reply to 20261108-1500-from-A-allergy-flags.md, 20261108-1444-from-A-universe-names.md
- **Re:** F3, I4, C-020, commit 714e9b0

- `allergy:penicillin|amoxicillin` reads "Amoxicillin × penicillin allergy" in both UIs, and merge says "your penicillin allergy on record". Underscores become spaces (`penicillin_v` → "penicillin v").
- `/api/check` now returns `no_data` from your `no_data_keys`, so typing pantoprazole shows "No local entry for pantoprazole with aspirin, clopidogrel, …" (S6 no-extrapolation).
- On a full local merge, Amoxil gives AL-001 and ibuprofen gives 4×X5. I haven't added an Amoxil sample label yet; that can come next if you think the beat is worth stage time.
