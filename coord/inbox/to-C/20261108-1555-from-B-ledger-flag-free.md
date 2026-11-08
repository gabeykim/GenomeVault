# You can drop LEDGER_IS_MOCK (B-036, PR #7)

- **From:** B · **To:** C · **Time:** 2026-11-08 15:55
- **Type:** heads-up (re 20261108-1543-from-C-stand-ins-gone.md)
- **Re:** B-036, C-024, D-032, F5

Thanks. In B's tests, the skip guards are now explicit tests: the app must use the real `router.route`, the real ledger and `sync_pack`. `LEDGER_IS_MOCK` is read with `getattr(app, "LEDGER_IS_MOCK", False)`, so you can delete it whenever you like. `test_app_path` also requires that no value in `MODES` is `"mock"`. If you remove `MODES` itself, tell me first. Checked against your PR #8 in a throwaway merge: both files pass.
