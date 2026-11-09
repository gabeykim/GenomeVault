"""B-073: why C's consent box (D-041 single send) rarely appears with GV_TAIL on.

Every key A's rules can produce is either in a fixed partition (core or tail, sent in its bucket of 8, I5)
or an allergy key, which never goes to the cloud (generalize -> []). Every drug pair over A's vocabulary is
in the tail. So with today's data no real question reaches `single_candidates`; it is a safety net for
keys A may add later. If A adds a cloud key outside both partitions, the first test fails and names it.
"""
import pytest

from core import kb, ledger, router
from core.generalize import kind_of
from core.interfaces import load_profile
from core.rules import all_keys, check_all


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DEMO_LIVE_FALLBACK"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("GV_TAIL", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


def _allergy(key: str) -> bool:
    return key.split("|", 1)[0].startswith("allergy:")


def test_every_rule_key_is_partitioned_or_allergy():
    outside = sorted(k for k in all_keys() if not router._in_partition(k) and not _allergy(k))
    assert outside == [], f"cloud keys outside core+tail would reach the single-send box: {outside}"


def test_allergy_keys_never_generalize():
    allergy = [k for k in all_keys() if _allergy(k)]
    assert allergy and all(kind_of(k) == "gene_drug" for k in allergy)   # shape only; engine decides
    from core.contracts import Flag
    from core.generalize import generalize
    for k in allergy:
        assert generalize(Flag(id="A", key=k, severity="high", engine="allergy",
                               evidence=[], needs_cloud=True)) == []


QUESTIONS = [
    "Can I take amoxicillin with warfarin?",
    "Is my clopidogrel ok with my genes?",
    "Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?",
    "What about my potassium and lisinopril?",
    "Can I take ibuprofen with my meds?",
]


@pytest.mark.parametrize("q", QUESTIONS)
def test_real_questions_with_alex_flags_have_no_single_candidate(q):
    flags = check_all(load_profile())
    assert router.single_candidates(q, flags) == []
    assert ledger.feed(0) == []                       # local parse only, nothing recorded
