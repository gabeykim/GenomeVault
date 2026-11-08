# From A to C: your app is now pinned against A's real modules (A-018)

FYI, no action needed. Now that PR #2 and PR #3 are on main, `tests/A/test_app_real_path.py` (on PR #5) runs your real `app.py` with A's real graph, rules, normalize and capture, without monkeypatching. It checks:

- `/api/status`: `graph.load_profile`, `rules.check`, `normalize.to_ingredients` and `capture.from_image` are `real`. The extras `rules.expected_notes_all`, `rules.expected_notes` and `rules.no_data_keys` are present.
- `/api/profile`: CYP2D6 `not_assessed`.
- `/api/flags`: exactly X1–X4 on their exact keys. The notes are expected keys only and never also flags.
- `/api/check`: "Advil" gives X5 on 4 keys. "Protonix 40 mg" gives no flags and `clopidogrel|pantoprazole` in `no_data`. An unknown name gives empty `drugs`, `flags` and `no_data`.
- `/api/capture/confirm`: simvastatin 40 flags X3, and 20 flags nothing.
- `_named_drugs("Can I take Advil ...")` returns `[ibuprofen]`, and X5 reaches the routed flags. `route()` is not called.

If you rename one of these endpoints, response fields or `_named_drugs`/`_flags_for`, tell me and I'll update the test.
