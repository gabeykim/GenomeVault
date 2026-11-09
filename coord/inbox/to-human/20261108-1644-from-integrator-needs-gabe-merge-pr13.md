# Needs Gabe: merge PR #13 (Codespaces demo link) after #11, then boot it once

- **From:** integrator (loop) · **To:** Gabe · **Time:** 2026-11-08 16:44
- **Type:** action request (merge + admin setting)
- **Re:** D-039, proposals/20261108-1640-C-codespaces-demo.md, to-integrator/20261108-1640-from-C-codespaces-pr13.md, PRs #11 and #13

I accepted the proposal (D-039). It is repo config only, CI passes on #13, and GitHub reports it mergeable. I merged nothing. The loop doesn't merge PRs, and these steps need you:

1. Merge **#11** (C) first, then **#13**, using merge commits. #13 works without #11, but its phone link needs C's `82a7205`.
2. Open `https://codespaces.new/gabeykim/GenomeVault?quickstart=1`, wait about 2 minutes, and check that port 8000 opens the app and that `/phone` loads. If it doesn't boot, tell C.
3. Under the repo's About → Website, set the same link. This needs admin.
4. If the repo is **private**, only collaborators can open the link, so judges can't use it. Make it public before you share the link, or leave it out of the submission.

Small difference from `make demo`: the container sets `GV_COVER_INTERVAL_S=20` (default 60) so cover traffic shows up quickly. I told B.
