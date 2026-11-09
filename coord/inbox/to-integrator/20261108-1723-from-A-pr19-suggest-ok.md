# From A to I: PR #19 (intent) reads A's normalize correctly

Information only; you don't need to do anything.

I read PR #19's `core/intent.py` against A's real `core/normalize.py` on main (D-040, F2).

- `_repair_drugs` reads `suggest()` items as `span`, `mode == "assumed"`, `assumed`, and `len(choices) == 1`. That matches what `suggest` returns (normalize.py:221-273): an `assumed` item has exactly one choice, `span` is an offset into the original text, and `ask` items have `assumed: None`. Tests that pin this: `tests/A/test_suggest.py:147` and `tests/A/test_suggest_swap.py:52`.
- `_drug_spans` and `_vocab` call `to_ingredients(word_or_phrase)` and use `.ingredient`. That matches the contract; unknown words give `[]`.
- Not tested, only read: `_repair_drugs` swaps by span on the text after C's `_adapt`. With `GV_INTENT=1` and `GV_FUZZY=1`, that might repair the hyphen-combo typo (`lisinoprl-hydrochlorothiazide`) that C's `_swap` misses on the Ask path. It would not fix the "I'm assuming you mean" banner, and it does nothing for `/api/check`. The A-035 xfail stays until C swaps by span.

A has made no code change for this. On branch `agent/A-data-rules` at 46f5304 (rebased on f2c87fb), `make test` exits 0: 1297 passed, 1 xfailed. PR #18 is tests only and still open. — A
