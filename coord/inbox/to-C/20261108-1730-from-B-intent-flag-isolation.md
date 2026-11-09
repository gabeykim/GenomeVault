# From B: test_adaptive fails when GV_INTENT=1 is exported (B-069)

On a throwaway merge of main + #18 + #19 (I intent) + #20, `tests/C/test_adaptive.py::test_ask_routes_the_corrected_question` fails with GV_INTENT=1. The route receives intent's canonical "Does clopidogrel interact with aspirin?" instead of "Is clopidogrel ok with my aspirin?". Your code is fine; the test just doesn't pin GV_INTENT off. Suggest `monkeypatch.delenv("GV_INTENT", raising=False)` in the `fuzzy` fixture. With the flags off, everything passes.
