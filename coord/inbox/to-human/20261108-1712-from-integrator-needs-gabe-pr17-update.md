# Needs Gabe: PR #17 changed since the 1709 merge note

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 17:12
- **Type:** info (update to an open merge request)
- **Re:** to-human/20261108-1709-from-integrator-needs-gabe-merge-pr14-17.md, to-integrator/20261108-1716-from-A-sound-alikes-done.md, D-040, D-041, D-042

The 1709 note said #17 had 2 commits and 1219 passing tests. It now has **3 commits** (head `6088d6b`), CI green, and A reports 1229 passed. The new commit makes `suggest()` count sound-alike spellings as 1 edit: `ibuprophen` is now assumed to be ibuprofen, and `plavicks` asks (plavix / paxil / taxol). The return shape is unchanged, so D-041 stands. It still sits behind `GV_FUZZY`, default OFF.

Recommendation unchanged: merge #16, #15, #17 and #14 with merge commits, #16 first. Nothing else changed in #14–#16.
