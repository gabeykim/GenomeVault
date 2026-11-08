"""B queue 2 done-when: no value from Alex's profile appears in any Topic (P6.3, I3)."""
import json
import re

import pytest

from core.contracts import Flag
from core.decoys import universe
from core.generalize import generalize, topic_for_key
from core.interfaces import MOCKS, load_profile


def _alex_values() -> list[str]:
    p = load_profile()
    vals = set(p.genotypes.values()) | set(p.phenotypes.values())
    vals |= set(p.conditions) | set(p.allergies)
    for lab in p.labs:
        vals.add(lab.date.isoformat())
        vals.add(f"{lab.value:g}")
    for d in p.meds:
        if d.dose_mg is not None:
            vals.add(f"{d.dose_mg:g}")
    return sorted(vals)


def _leaks(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for v in _alex_values():
        if re.fullmatch(r"[0-9.]+", v):
            if re.search(rf"(?<![\w.]){re.escape(v)}(?![\w]|\.\d)", text):
                hits.append(v)
        elif v.lower() in low:
            hits.append(v)
    return hits


def _mock_flags() -> list[Flag]:
    return [Flag.model_validate(f) for f in json.loads((MOCKS / "flags.json").read_text())]


@pytest.mark.parametrize("key", universe())
def test_every_universe_key_generalizes_without_alex_values(key):
    t = topic_for_key(key)
    assert t.key == key
    assert _leaks(t.text) == [], (key, t.text)


@pytest.mark.parametrize("key", universe())
def test_no_numbers_or_thresholds_in_topic_text(key):
    text = topic_for_key(key).text
    # strip gene symbols (CYP2C19, HLA-B ...) then no digit may remain
    stripped = re.sub(r"\b[A-Z][A-Z0-9-]*\d[A-Z0-9-]*\b", "", text)
    assert not re.search(r"\d", stripped), text
    assert "<" not in text and ">" not in text and "*" not in text


def test_alex_flags_one_topic_each_and_clean():
    for f in _mock_flags():
        topics = generalize(f)
        assert len(topics) == 1 and topics[0].key == f.key
        assert _leaks(topics[0].text) == []


def test_phenotype_phrased_for_all_phenotypes():
    text = topic_for_key("CYP2C19:poor_metabolizer|clopidogrel").text
    for ph in ("poor", "intermediate", "normal", "rapid", "ultrarapid"):
        assert ph in text
    assert "poor_metabolizer" not in text


def test_lab_phrased_for_all_bands():
    text = topic_for_key("lisinopril|potassium>5.0").text
    assert "5.0" not in text and "low" in text and "high" in text


def test_allergy_flag_never_generalized():
    f = Flag(id="Z", key="penicillin|amoxicillin", severity="high", engine="allergy", evidence=[])
    assert generalize(f) == []


def test_malformed_key_rejected():
    with pytest.raises(ValueError):
        topic_for_key("a|b|c")
