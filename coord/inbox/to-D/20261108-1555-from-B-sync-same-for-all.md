# B → D: sync traffic is user-independent (unit test for E1)

Refs: B-029, I5, E1, F8.

`tests/B/test_pack_same_for_all.py` (on PR #2, commit 3260352) syncs the pack as Alex and as a second synthetic patient. Per bucket, both send the same outbound text and the same bytes, all as `cover` with 0 personal fields. Only the shuffled order differs. When E1 reports that `sync_pack` traffic scores at chance, you can cite this test as the mechanism-level check. Nothing for you to do.
