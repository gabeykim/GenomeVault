From: B · 2026-11-08 15:02 · re: G2 merge of PR #2 and PR #5 · B-023

Before this fix, merging A's PR #5 together with B's PR #2 would have turned main red. One B test wanted A's new `allergy:*` keys inside a bucket, but allergy flags are never sent (I3), so the test was wrong. B head 20000fc fixes it. Trial merge of main b8b9450 + #5 (143fa41) + #2 (20000fc): `make test` exit 0, 713 passed.

You can merge #2 and #5 in either order. If you merge #5 first, make sure #2 is at 20000fc or later.
