# From B: adaptive-questions proposal (20261108-1655), B's parts

- B has started nothing from this proposal; it needs your ruling first (touches I4, I5; AGENTS.md §5, §8).
- If accepted, B will build, each behind its flag and default OFF so the demo path is unchanged:
  1. Part 3 `GV_DEMO_LIVE_FALLBACK=1` first (small: a DEMO=1 cache miss goes live only when online; forced offline still wins).
  2. Part 2 `GV_TAIL=1` next: committed `data/buckets/tail-v1.json` (k = 8, seeded once, same for every user, never built from a query), routed through every P6 step and the ledger with label `tail`.
- If either part is not green by 18:00 it ships OFF, per the proposal's timebox.
- Please say in the ruling whether the `tail` ledger label and the "single, not hidden" consent path (part 4) belong in CONTRACTS, since C would read them.
- PR #15 (tests only, c4c4998, 2/2 green) is still ready to merge. make test exit 0, 1178 passed.
