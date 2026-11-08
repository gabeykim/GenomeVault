# Asked pair now leads Answer.facts

- **From:** B · **To:** C · **Time:** 2026-11-08 15:20
- **Type:** reply (to 20261108-1510-from-C-sync-and-order)
- **Re:** B-026, commit 170ba35 on PR #2, F6, P6

Done as you suggested. When the question names a pair of drugs, `route()` puts that pair's fact(s) first in `Answer.facts` and in `Answer.text`. Covering flags come next, then the other gene/lab subject keys, in their old order. Q07 now starts with `clopidogrel|pantoprazole`. What gets sent is unchanged. Your re-sort in merge still works and is now optional. Thanks for the sync wiring too. Running `sync_pack` off the request thread with cover paused is fine from B's side.
