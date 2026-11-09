# Needs Gabe: merge PRs #14–#17 (D-040 parts behind flags, all default OFF)

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 17:09
- **Type:** action request (merge)
- **Re:** to-integrator/20261108-1659-from-C-pr16-ask-input-fix.md, 20261108-1706-from-A-pr17-ready.md, 20261108-1708-from-C-d040-part4.md, 20261108-1656-from-B-adaptive-questions-ready.md, to-human/20261108-1658-…-merge-pr14-pr15.md, D-040, D-041, G5

I merged nothing. CI passes on all four. main is green after this pass: `make test` 1178 passed (including the new D-041 contract test), `check_network.sh` ok.

- **#16 (C, `agent/C-app-ui`, 3 commits): merge first.** It fixes a live bug: the hidden C-027 title caption was catching clicks over the Ask input, so typing in Ask didn't work. Adds `Cache-Control: no-cache` middleware in `app.py` for UI files. It also includes D-040 part 4 (banner, chips, consent box, ledger labels), which stays dormant unless A's and B's flags are on. C reports 1191 passed. Reload any open tab after merging.
- **#15 (B, 3 commits):** replaces the tests-only version from the 1658 note. It adds D-040 parts 2 and 3: `GV_TAIL` (committed `data/buckets/tail-v1.json` plus its builder, single send) and `GV_DEMO_LIVE_FALLBACK`, both default OFF. The diff is large (+15k lines), but nearly all of it is the generated tail JSON.
- **#17 (A, 2 commits):** `normalize.suggest` behind `GV_FUZZY`, default OFF, plus `data/rules/lookalikes.json`. A reports 1219 passed.
- **#14 (D):** wording/G4 docs only. Same as the 1658 note.

My recommendation: merge all four with merge commits, #16 first. They touch separate owned paths. After merging, run `make test`, and decide the D-040 flags at 18:00 once C's end-to-end run is done. D-041 (this pass) only records the A/B function shapes in CONTRACTS, with flag-off stubs. No invariant or type change.
