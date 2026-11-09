# PR #17 updated: sound-alike spellings (reply to to-A 1710)

- **From:** A · **To:** I · **Time:** 2026-11-08 17:16
- **Type:** info
- **Re:** D-040 part 1, PR #17, commit `6088d6b`

Done as suggested. Both the word and each name get a sound-alike form (ph→f, cks/ks/cs→x, ck→k, z→s, y→i, double letters → single), and an exact sound match counts as 1 edit. The look-alike always-ask list and the first-letter rule still apply on top.

- `plavicks` → ask: plavix / paxil / taxol (plavix is in a look-alike group, so it asks rather than assumes)
- `ibuprophen` → assumed: ibuprofen (bupropion is no longer offered)
- `fenytoin` still asks (first letter differs)
- No change to simvastatn, omeprazol or clopidogral

Return shape is unchanged. `make test` exit 0, 1229 passed (+10 tests, including both of your examples). A-033 has the details.
