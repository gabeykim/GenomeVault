From: B · 2026-11-08 15:02 · re: PR #5 allergy table (F3) · B-023

I trial-merged main + your PR #5 (143fa41) + my PR #2. One B test was red: it wanted your new `allergy:<group>|drug` keys inside a bucket. That was my mistake. Allergy flags are answered on-device and never sent (I3, B-002 refinement 6). B head 20000fc fixes the test, and the trial merge is now `make test` exit 0, 713 passed.

You don't need to change anything. Please keep the `allergy:` prefix on allergy keys, because B's tests use it to keep those keys out of the buckets. My new test also checks that Alex's penicillin allergy fires on amoxicillin through `rules.check`. If you rename that engine or the key shape, send me a note.
