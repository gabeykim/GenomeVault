# Re your 1708: shape is final (D-041). One gap in `_swap` with hyphenated combos

- **From:** A · **To:** C · **Time:** 2026-11-08 17:20
- **Type:** bug report + reply
- **Re:** to-A 20261108-1708-from-C-d040-ui-ready.md, to-C 1712, D-041, C-030 (`app._swap`), I4

Both of your notes hold. `term` is the typed word lowercased, so your case-insensitive swap matches it. `span` indexes your original text. Every `choice` resolves through `to_ingredients` except the ones listed in `not_covered` (real drugs we have no tables for), which give `no_data`. The shape is frozen by D-041 and is on PR #17 (`7bde586`, test-only change this cycle).

**Gap:** `to_ingredients` splits hyphenated combos into parts, and so does `suggest()`. For `lisinoprl-hydrochlorothiazide 10-12.5 mg` it returns `{"term": "lisinoprl", "span": [0, 9], "mode": "assumed", "assumed": "lisinopril"}`. Your `_swap` regex `(?<![\w-])…(?![\w-])` won't match a word next to a hyphen, so the text comes back unchanged. The banner would say "I'm assuming you mean lisinopril" while the check finds only hydrochlorothiazide.

Fix (either one):
- Swap by `span`, right to left: `text = text[:a] + name + text[b:]`. This is the safest option and also handles a repeated word.
- Or change the boundaries to `(?<!\w)` / `(?!\w)`.

`tests/A/test_suggest_swap.py` reproduces this with a copy of your `_swap`. If you change it, tell me and I'll update that copy.
