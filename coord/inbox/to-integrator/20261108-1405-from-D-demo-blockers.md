# Demo walk-through on all four branches: S4 and S6 are blocked on the demo cache

- **From:** D · **To:** integrator · **Time:** 2026-11-08 14:05
- **Type:** request (supports 20261108-1350-from-B-cloud-cache.md)
- **Re:** I8, P8 S4/S6, G2, D-006, commit eddea32

I merged A+B+C+D locally and walked the demo in demo mode (`DEMO=1`). The privacy path works: Q18 sends b01 (1,248 B) and b05 (959 B), 0 personal fields, and four questions left 7 buckets and 0 personal fields. But with `mocks/cloud_cache/` empty:

- **S4:** every Ask answers `no_data`, so there's no personalized answer to read out.
- **S6 "learns":** nothing reaches the KB, so Q19 re-sends b01 + b05 instead of a 0-byte `kb_hit`. "Facts learned" stays at 0, and even `router.sync_pack()` leaves offline at 10/20.

So B's request to record the cache (`python -m core.cloud record mocks/cloud_cache`, before G2 at 16:00) is what unblocks both beats. B has since made `data/buckets/v2.json` the default (B-011), so please record against v2. Rehearsal check, now in `slides/demo_script.md`: restart `make demo`, ask Q18 then Q19, and confirm Q19 logs a 0-byte `kb_hit`.

FYI: A's loop stopped at 14:03 (`coord/inbox/to-human/20261108-1403-from-A-loop-stopped.md`). A's PR #1 is marked ready for G1.
