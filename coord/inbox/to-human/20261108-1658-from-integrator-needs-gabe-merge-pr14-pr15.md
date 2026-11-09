# Needs Gabe: merge PRs #14 (D) and #15 (B) before G5

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 16:58
- **Type:** action request (merge)
- **Re:** to-integrator/20261108-1651-from-D-pr14.md, to-integrator/20261108-1700-from-B-cover-20s-ok.md, D-016, D-038, D-039, G5

Both PRs are small, CI passes on both, and I merged nothing.

- **#14 (D, `agent/D-eval`, 3 commits):** wording-only changes to the headers of 6 docs/slides files (they now cite G4 instead of the dry run), plus the G4 result in `docs/G4.md`. No figure changes. D reports 1177 passed and the gate at 22 pass, 0 warn, 0 fail on current main.
- **#15 (B, `agent/B-privacy-router`, 1 commit `c4c4998`):** tests only. It checks that the cover loop waits 10 to 30 s per tick with jitter and sends one whole bucket each time, which covers D-039's `GV_COVER_INTERVAL_S=20`. B reports 1178 passed.

Use merge commits. They touch separate paths, so the order doesn't matter.

Also checked: B's I4 fix `ccf2c4f` (an off-list pair read "checked on your device") is already on main through PR #10. Nothing more is needed for it.
