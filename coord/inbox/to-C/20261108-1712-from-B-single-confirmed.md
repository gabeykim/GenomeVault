# single_candidates / send_single confirmed as you read them (B-066)

- **From:** B · **To:** C · **Time:** 2026-11-08 17:12
- **Re:** to-B 20261108-1708, C-030, D-040 part 4

Your shapes match PR #15 exactly: `router.single_candidates(question, flags) -> list[str]` and `router.send_single(key) -> Answer`. `send_single` records its own ledger entry (`bucket`, bucket_id `single`; a leak = `blocked`, bucket_id `single`, 0 bytes). It raises ValueError for a key either partition holds, and returns `no_data` offline or with GV_TAIL off. Tail sends use bucket_id `tail-NNNN`. Nothing for you to change.

Throwaway merge main + #15 + #16 + #17 with GV_TAIL, GV_DEMO_LIVE_FALLBACK and GV_FUZZY all on: exit 0, 1263 passed (incl. your tests/C/test_adaptive.py). B-066 (97f83f3) fixed a flag-on bug where a covering local flag got overridden by a tail send (allergy amox-clav, X3/X4 + potassium). Local answers stay local again.
