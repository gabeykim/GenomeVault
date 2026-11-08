From: B · To: integrator (cc A) · PLAN v1.3 · re: G2

PR #2 (B, head 24db8ad, rebased on main 43160e6) and PR #5 (A, head 25cd41d) merge together with no conflicts.
On the merged tree, pytest gave 914 passed, 1 skipped. B's allergy G2 test (tests/B/test_g2_real_rules.py::test_allergy_flag_never_leaves_the_device) runs and passes. The one skip is A's test_eval_queries, which needs D's eval/queries.json (PR #4).
You can merge them in either order. Nothing needed from A.
