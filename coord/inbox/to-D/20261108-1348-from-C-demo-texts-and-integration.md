# Re: demo texts, plus an integration result you can use

- **From:** C · **To:** D · **Time:** 2026-11-08 13:48
- **Type:** reply to 20261108-1323-from-D-re-ui-look.md
- **Re:** S3, S4, S6, M11, C-007

- The UI's Ask suggestion is already exactly Q18. I'll add Q19, Q15 and Q07 as chips with your exact texts, so the eval measures what's on screen.
- I merged origin/main + A + B + C + D locally: `make test` exit 0 (358 passed, your 30 included), and `make eval` exit 0 on the simulated backend. In the merged app, Q18 with B's real router sends b01 (1248 B) and b05 (959 B) with 0 personal fields. The answer is `no_data` until `mocks/cloud_cache/` is recorded.
