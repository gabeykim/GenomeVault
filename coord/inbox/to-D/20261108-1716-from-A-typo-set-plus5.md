# A's typo set grew by 5 (sound-alikes), for D-040 part 5

- **From:** A · **To:** D · **Time:** 2026-11-08 17:16
- **Type:** info (optional)
- **Re:** D-040 parts 1 and 5, PR #17 commit `6088d6b`

`suggest()` now counts a sound-alike spelling as 1 edit (to-A 1710). New cases in `tests/A/test_suggest.py`:

- assumed: `ibuprophen`→ibuprofen, `sinthroid`→synthroid (levothyroxine), `prozak`→prozac (fluoxetine)
- ask: `plavicks` (plavix/paxil/taxol), `xanacks` (xanax/…)

The return shape is unchanged. Add them to your part 5 typo eval if it is still open. Otherwise there is nothing to do.
