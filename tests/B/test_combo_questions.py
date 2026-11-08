"""Combination products in a question (A-014): "ezetimibe-simvastatin 10-40 mg", "amox-clav".

A's normalizer now reads a combination as several ingredients, some of which are outside the bucket
universe (ezetimibe, clavulanate). The router must only ever ask about universe drugs, never send the
outside ingredient's name or the question's strengths (I3), and never call such a question "known"
because of a flag for a different drug (I4).
"""
import json

import pytest

from core import kb, ledger, router
from core.contracts import Drug, Flag
from core.decoys import load_buckets

ALLERGY = Flag(id="AL-001", key="penicillin|amoxicillin", severity="high", engine="allergy",
               evidence=["penicillin allergy"], needs_cloud=True)

_COMBOS = {  # what A-014's to_ingredients returns for these questions (stand-in until PR #5 merges)
    "ezetimibe-simvastatin": [Drug(ingredient="ezetimibe", dose_mg=10), Drug(ingredient="simvastatin", dose_mg=40)],
    "amox-clav": [Drug(ingredient="amoxicillin", dose_mg=None), Drug(ingredient="clavulanate", dose_mg=None)],
}


def _stub_to_ingredients(text: str) -> list[Drug]:
    t = text.lower()
    out = [d for name, ds in _COMBOS.items() if name in t for d in ds]
    if "clopidogrel" in t or "plavix" in t:
        out.append(Drug(ingredient="clopidogrel", dose_mg=None))
    return out


@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(router.cloud, "_forced", None)
    import core.normalize as normalize
    monkeypatch.setattr(normalize, "to_ingredients", _stub_to_ingredients)
    for b in load_buckets():
        (tmp_path / f"{b.id}.json").write_text(json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


def _outbound() -> list[str]:
    return [t for e in ledger.feed(0) for t in ledger.outbound(e.seq)]


def test_combo_names_only_its_universe_ingredient():
    q = "Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?"
    assert router._named_drugs(q) == ["clopidogrel", "simvastatin"]
    assert router._question_keys(q) == ["clopidogrel|simvastatin"]


def test_combo_question_online_sends_no_outside_name_or_strength():
    q = "Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?"
    a = router.route(q, [])
    assert a.sent_to_cloud
    assert all(e.personal_fields_sent == 0 for e in ledger.feed(0))
    for t in _outbound():
        low = t.lower()
        assert "ezetimibe" not in low and "10-40" not in low and q.lower() not in low


def test_combo_question_offline_is_no_data(monkeypatch):
    monkeypatch.delenv("DEMO")
    a = router.route("Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?", [])
    assert a.state == "no_data" and not a.sent_to_cloud and a.text == router.OFFLINE_TEXT
    assert ledger.feed(0) == [] or all(e.bytes_out == 0 for e in ledger.feed(0))


def test_amox_clav_with_allergy_flag_stays_local():
    a = router.route("Can I take amox-clav?", [ALLERGY])
    assert not a.sent_to_cloud
    assert [e.kind for e in ledger.feed(0)] == ["local_only"]
    assert all(e.bytes_out == 0 for e in ledger.feed(0))


def test_amox_clav_never_sends_clavulanate():
    router.route("Can I take amox-clav with Plavix?", [])
    for t in _outbound():
        assert "clavulanate" not in t.lower() and "amox-clav" not in t.lower()
