"""Wording red team for B's I7 filter (B-013). The case file is checked here; scores are measurements, not
asserted, except that the plain cases must be caught whenever B's validator is present."""
import importlib

import pytest

from eval import wording


def test_cases_well_formed():
    cases = wording.load_cases()
    assert len({c["id"] for c in cases}) == len(cases) >= 30
    assert {c["expect"] for c in cases} == {"reject", "accept"}
    assert all(c["text"].strip() for c in cases)
    assert sum(c["expect"] == "reject" for c in cases) >= 20


def test_runs_with_or_without_bs_validator():
    r = wording.run(write=False)
    try:
        importlib.import_module("core.validator").wording_problems
    except (ImportError, AttributeError):
        assert r["status"].startswith("skipped")
        pytest.skip("B's validator is not in this build")
    assert r["status"] == "ran"
    plain = r["by_family"]["plain"]
    assert plain["caught"] == plain["of"]          # the cases B-013 was built for
