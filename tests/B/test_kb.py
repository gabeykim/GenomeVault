import json
from datetime import date, timedelta

import pytest

from core import kb, ledger, router
from core.contracts import Fact, Flag
from core.decoys import bucket_for

TODAY = date(2026, 11, 8)
X1 = Flag(id="X1", key="CYP2C19:poor_metabolizer|clopidogrel", severity="high", engine="gene_drug",
          evidence=["CYP2C19 poor metabolizer"], needs_cloud=True)


def fact(key="clopidogrel|omeprazole", tier="cloud", text="t", fetched=TODAY, days=30):
    return Fact(key=key, text=text, tier=tier, source="s", fetched=fetched,
                expires=fetched + timedelta(days=days))


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH"):
        monkeypatch.delenv(v, raising=False)
    b = bucket_for(X1.key)
    (tmp_path / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    kb.reset()
    ledger.reset()
    yield
    kb.reset()
    ledger.reset()


def test_exact_key_only():
    kb.put(fact("clopidogrel|omeprazole"))
    assert kb.get("clopidogrel|omeprazole", TODAY) is not None
    for near in ("clopidogrel|pantoprazole", "Clopidogrel|omeprazole", "clopidogrel", "omeprazole|clopidogrel "):
        assert kb.get(near, TODAY) is None  # I4: no extrapolation, no fuzzy match


def test_expired_fact_is_a_miss():
    kb.put(fact(days=5))
    assert kb.get("clopidogrel|omeprazole", TODAY + timedelta(days=5)) is not None
    assert kb.get("clopidogrel|omeprazole", TODAY + timedelta(days=6)) is None
    assert kb.stats(TODAY + timedelta(days=6)) == {"total": 1, "fresh": 0, "expired": 1, "curated": 0, "cloud": 0}


def test_cloud_never_overwrites_curated():
    assert kb.put(fact(tier="curated", text="curated", days=365))
    assert not kb.put(fact(tier="cloud", text="cloud", fetched=TODAY + timedelta(days=1)))
    assert kb.get("clopidogrel|omeprazole", TODAY).text == "curated"


def test_curated_overwrites_cloud_and_newer_overwrites_older():
    kb.put(fact(tier="cloud", text="old", fetched=TODAY))
    assert not kb.put(fact(tier="cloud", text="older", fetched=TODAY - timedelta(days=1)))
    assert kb.put(fact(tier="cloud", text="new", fetched=TODAY + timedelta(days=1)))
    assert kb.get("clopidogrel|omeprazole", TODAY + timedelta(days=1)).text == "new"
    assert kb.put(fact(tier="curated", text="curated"))
    assert kb.get("clopidogrel|omeprazole", TODAY).tier == "curated"


def test_persists_across_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("GV_KB_PATH", str(tmp_path / "kb" / "kb.json"))
    kb.reset()
    kb.put_many([fact("a|b"), fact("c|d", tier="curated")])
    kb.reset()  # simulated restart
    assert kb.get("a|b", TODAY).tier == "cloud"
    assert kb.get("c|d", TODAY).tier == "curated"
    assert [f.key for f in kb.all_facts()] == ["a|b", "c|d"]
    assert kb.remove("a|b") and not kb.remove("a|b")
    kb.reset()
    assert kb.get("a|b", TODAY) is None


def test_bucket_answers_all_stored_and_repeat_is_kb_hit_with_zero_bytes():
    b = bucket_for(X1.key)
    first = router.route("What does my genotype mean for clopidogrel?", [X1])
    assert first.sent_to_cloud and first.state == "known"
    for k in b.keys:  # all 8 answers stored, decoys included (P6.5, F6)
        assert kb.get(k) is not None and kb.get(k).tier == "cloud"

    n = len(ledger.feed(0))
    again = router.route("What does my genotype mean for clopidogrel?", [X1])
    assert again.state == "known" and not again.sent_to_cloud
    assert [f.key for f in again.facts] == [X1.key]
    new = ledger.feed(n)
    assert [e.kind for e in new] == ["kb_hit"] and new[0].bytes_out == 0


def test_decoy_key_answered_from_kb_without_sending():
    b = bucket_for(X1.key)
    router.route("q", [X1])
    decoy = next(k for k in b.keys if k != X1.key)
    flag = Flag(id="Z", key=decoy, severity="medium", engine="drug_drug", evidence=[], needs_cloud=True)
    n = len(ledger.feed(0))
    a = router.route("q", [flag])
    assert not a.sent_to_cloud and a.facts[0].key == decoy
    assert all(e.bytes_out == 0 for e in ledger.feed(n))
