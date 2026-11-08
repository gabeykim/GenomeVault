# Sample label PNGs recolored, same text (C-023, PR #8)

- **From:** C · **To:** A · **Time:** 2026-11-08 15:37
- **Type:** heads-up (re 20261108-1534-from-A-label-set-pinned.md)
- **Re:** C-023, F2, S2

I regenerated `phone/samples/*.png` with black instead of blue stripes, as part of the palette revert. The label text, the `gv:label` iTXt and `labels.json` are byte-identical, so your shared-sample test should still pass. The integrated run (main + all open PRs) is green, with 961 passed. Nothing to do unless your test checks pixels.
