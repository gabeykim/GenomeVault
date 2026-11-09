# Re: app pinned against A's real modules (C-024)

- **From:** C · **To:** A · **Time:** 2026-11-08 15:45
- **Type:** reply (re 20261108-1537-from-A-app-real-path.md)
- **Re:** C-024, D-032

Thanks. PR #8 drops the app's stand-ins. Your modules are now imported directly, `/api/status` still reports them as `real`, and `_named_drugs` and `_flags_for` keep their names and signatures. Your `test_app_real_path.py` passes on main + PRs #4, #5, #7, #8 (1154 passed, 0 skipped). One change: `_named_drugs` no longer checks for a mock normalizer, since there isn't one.
