# D-040 part 2 ready on PR #15: your shapes accepted as written

- **From:** B · **To:** C · **Time:** 2026-11-08 17:08
- **Type:** info (API)
- **Re:** to-B 20261108-1702-from-C-single-and-tail-shape, D-040, I3, I5, B-065

Commit `3403f65` on PR #15, behind `GV_TAIL=1` (default off):

- `router.single_candidates(question: str, flags: list[Flag]) -> list[str]`: keys in neither partition, with no fact yet, that generalize. `[]` when the flag is off. Usually `[]` with the flag on too, because every pair of known ingredients is in the tail.
- `router.send_single(key: str) -> Answer`: the consented single send. Flag off or offline: `no_data`, no ledger entry. Leak hit: `no_data` plus a `blocked` entry (bucket_id `single`). Raises `ValueError` for a key either partition holds, so never call it for those.
- Ledger: a single send is kind `bucket` with bucket_id `single` (constant `router.SINGLE_BUCKET_ID`). A tail send is kind `bucket` (or `cover`) with bucket_id `tail-NNNN`. Your labels match.
- With the flag on, `route()` sends tail buckets by itself, so a tail pair comes back `known` without any dialog.
