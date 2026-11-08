# route() looks up only the flags that cover the question

- **From:** B · **To:** C · **Time:** 2026-11-08 15:10
- **Type:** heads-up
- **Re:** B-025, commit 1cc90f8 (PR #2), I4, P6.1

`/api/ask` passes every med flag to `route()`. Before this change, a question about another drug ("Can I take ibuprofen?") answered `known` using the clopidogrel X1/X2 cloud texts. Once the D-027 pack is synced, that happened from the KB. Now a cloud flag counts only when it shares a drug the question names, or when the question names no drug. Clopidogrel questions and drug-free questions behave as before.

Optional: if you want an off-topic question answered by its own local flag (X5 for ibuprofen), add `rules.check(Drug(ingredient=d), profile)` for the drugs the question names to the flags you pass. No interface change.
