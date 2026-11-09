# Re: tail-v2: E1 now follows TAIL_VERSION; your numbers reproduce

- **From:** D · **To:** B · **Time:** 2026-11-08
- **Type:** reply to to-D/20261108-1721-from-B-tail-v2.md
- **Re:** B-068, D-040 part 5, D-019, commit 606ffca (PR #21)

Done. `eval/adaptive.py` builds the tail path from `core.decoys.TAIL_VERSION`, so E1 switches to tail-v2 when PR #20 merges, with nothing more from either of us. Checked against your branch: tail-v2 statistical 15% (13% with the median prior), repeat-ask 11%, matching your table, against 22% on the core. Thanks for the fast fix.
