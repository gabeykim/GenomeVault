# PR #24: docs-only fix so the stage script matches demo-v1

- **From:** D · **To:** integrator (Gabe) · **Time:** 2026-11-08
- **Type:** bug fix request under FREEZE
- **Re:** FREEZE (17:49), PR #19 held, PR #21, D-021

PR #21 merged one commit early. With #19 held, three lines in `slides/presentation_script.md` described screens demo-v1 won't show: the "Four things to raise" lead line, "I took this as", and the old no-data wording. PR #24 fixes them, plus the demo and video scripts, and drops "This is Alex" since the deck has no picture of him. Slides only, three files; `DEMO=1 make test` 1311 passed. Please merge before the presenters rehearse. When you ping that main is final, D will re-run the beats against it.
