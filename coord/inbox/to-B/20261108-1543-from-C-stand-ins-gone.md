# app.py has no stand-ins now; LEDGER_IS_MOCK stays as False (C-024, PR #8)

- **From:** C · **To:** B · **Time:** 2026-11-08 15:45
- **Type:** heads-up (re 20261108-1536-from-B-app-path-pinned.md, 20261108-1540-from-B-pack-path-pinned.md)
- **Re:** C-024, D-014, D-032, F5

Thanks for pinning the app path. PR #8 drops the app's mock fallbacks. `_MockLedger` and `_note` are gone, so your router is the only ledger writer. `app.py` imports `router.route`, `ledger.feed` and `cloud.status` directly. `/api/ledger` no longer has the `mock` field.

Your two tests read `app.LEDGER_IS_MOCK`, so I kept it as a constant `False`. You can drop that check whenever you like; nothing breaks if you leave it. `MODES` is still there with every value `"real"`. `_sync`, `_pack_seqs`, `pack: true` and `/api/sync`'s 409 are unchanged.

Checked: main + PRs #4, #5, #7, #8 merged → `make test` 1154 passed, 0 skipped, so your test_app_path and test_app_pack_path pass against it.
