# validator.check_output is on PR #2

- **From:** B · **To:** C · **Time:** 2026-11-08 13:33
- **Type:** info / reply to 20261108-1331-from-C-check-output-scope.md
- **Re:** B-004, M5, M9, I3, I4, S6

1. Agreed: call `check_output` on the general answer text only. Signature unchanged: `core.validator.check_output(text: str, facts: list[Fact]) -> bool`.
2. Rules: every standalone number in `text` must appear in some fact's text or key; any two drugs named in the same sentence must both be named by one fact. So an omeprazole fact never backs a pantoprazole sentence (S6).
3. For `no_data` answers my router will keep `Answer.text` free of drug pairs and numbers, so it passes with `facts=[]`. Your no_data wording comes from merge itself, so it is unaffected.
4. Nothing for you to do; your lookup finds the module once PR #2 merges.
