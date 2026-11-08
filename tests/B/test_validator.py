"""B queue 3: outbound leakage check (I3) and output check (I4)."""
from datetime import date

import pytest

from core.contracts import Fact
from core.decoys import load_buckets, universe
from core.generalize import topic_for_key
from core.interfaces import load_profile
from core.validator import check_outbound, check_output, leaks, numbers_in


@pytest.fixture(scope="module")
def alex():
    return load_profile()


def _fact(key, text, tier="curated"):
    return Fact(key=key, text=text, tier=tier, source="test", fetched=date(2026, 11, 8),
                expires=date(2027, 11, 8))


# ------------------------------------------------------------ outbound (I3)

def test_every_generalized_topic_passes(alex):
    """No false positives: every Topic of every bucket is sendable."""
    for b in load_buckets():
        texts = [topic_for_key(k).text for k in b.keys]
        assert check_outbound(texts, alex), [(t, leaks(t, alex)) for t in texts if leaks(t, alex)]


@pytest.mark.parametrize("text", [
    "Clopidogrel 75 mg with omeprazole?",
    "Clopidogrel 75mg with omeprazole?",
    "Patient eGFR 48, was 62 last year",
    "potassium 5.2 mmol/L and lisinopril",
    "CYP2C19 *2/*2 and clopidogrel",
    "labs from 2026-10-28",
    "58-year-old after stent",
    "clopidogrel in a CYP2C19 poor metabolizer",
    "clopidogrel in a CYP2C19 poor_metabolizer",
    "SLCO1B1 decreased function and simvastatin",
    "statins with hyperlipidemia",
    "ibuprofen for someone with GERD",
    "allergic to Penicillin, can I take amoxicillin?",
    "CAD post stent and aspirin",
])
def test_personal_fields_are_blocked(alex, text):
    assert leaks(text, alex)
    assert not check_outbound(["a clean text", text], alex)


def test_gene_symbols_with_digits_are_not_numbers():
    assert numbers_in("CYP2C19 SLCO1B1 CYP2D6 HLA-B") == []
    assert numbers_in("dose 40.0 and 40") == ["40", "40"]


def test_allow_lets_bucket_drugs_through(alex):
    t = "Is an interaction between amoxicillin and penicillin listed?"
    assert any("allergy" in x for x in leaks(t, alex))
    assert not leaks(t, alex, allow=["penicillin", "amoxicillin"])
    # allow never waives the number rule
    assert leaks("penicillin 500", alex, allow=["penicillin"])


# ------------------------------------------------------------ output (I4)

def test_output_ok_when_pair_and_numbers_come_from_facts():
    f = _fact("clopidogrel|omeprazole",
              "Omeprazole reduces clopidogrel activation via CYP2C19; about 30% lower active metabolite.")
    assert check_output("Omeprazole can lower clopidogrel's effect by about 30%.", [f])


def test_output_rejects_number_not_in_facts():
    f = _fact("clopidogrel|omeprazole", "Omeprazole reduces clopidogrel activation via CYP2C19.")
    assert not check_output("Omeprazole lowers clopidogrel's effect by 45%.", [f])


def test_output_rejects_extrapolated_pair():
    """S6: a fact about omeprazole must not justify a claim about pantoprazole (I4)."""
    f = _fact("clopidogrel|omeprazole", "Omeprazole reduces clopidogrel activation via CYP2C19.")
    assert not check_output("Pantoprazole likewise reduces clopidogrel activation.", [f])
    assert not check_output("Pantoprazole reduces clopidogrel activation.", [])


def test_output_pairs_are_per_sentence():
    f1 = _fact("clopidogrel|omeprazole", "Omeprazole reduces clopidogrel activation.")
    f2 = _fact("lisinopril|potassium>5.0", "Lisinopril can raise potassium.")
    text = "Omeprazole reduces clopidogrel activation. Lisinopril can raise potassium."
    assert check_output(text, [f1, f2])
    assert not check_output("Omeprazole, clopidogrel and lisinopril together.", [f1, f2])


def test_output_gene_drug_fact_with_dose_band():
    f = _fact("SLCO1B1:decreased_function|simvastatin|dose>20mg",
              "Decreased SLCO1B1 function raises myopathy risk with simvastatin above 20 mg.")
    assert check_output("With decreased SLCO1B1 function, simvastatin above 20 mg raises myopathy risk.", [f])
    assert not check_output("Simvastatin 80 mg is risky.", [f])


def test_output_text_without_pairs_or_numbers_passes():
    assert check_output("No exact-key fact is stored for this question; ask your pharmacist.", [])


def test_universe_drugs_recognised():
    """Every drug in the bucket universe is known to the pair check."""
    from core.validator import _key_drugs, _universe_drugs
    drugs = set()
    for k in universe():
        drugs |= _key_drugs(k)
    assert drugs and drugs <= set(_universe_drugs())
