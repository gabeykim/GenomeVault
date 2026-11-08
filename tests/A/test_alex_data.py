"""A queue 1: Alex's synthetic data matches PLAN P5 and loads into Profile."""
import pathlib
from datetime import date

from core.contracts import Profile

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _profile() -> Profile:
    return Profile.model_validate_json((DATA / "alex_profile.json").read_text())


def _vcf() -> dict[str, tuple[str, str, str]]:
    """rsID -> (gene, allele, GT)."""
    out = {}
    for line in (DATA / "alex.vcf").read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split("\t")
        info = dict(kv.split("=", 1) for kv in cols[7].split(";"))
        out[cols[2]] = (info["GENE"], info["ALLELE"], cols[9])
    return out


def test_profile_loads_and_matches_p5():
    p = _profile()
    assert p.genotypes == {"CYP2C19": "*2/*2", "SLCO1B1": "*1/*5", "CYP2D6": "not_assessed",
                           "CYP2C9": "*1/*1", "VKORC1": "reference"}
    assert p.phenotypes["CYP2C19"] == "poor_metabolizer"
    assert p.phenotypes["SLCO1B1"] == "decreased_function"
    assert {(m.ingredient, m.dose_mg) for m in p.meds} == {
        ("aspirin", 81), ("clopidogrel", 75), ("omeprazole", 20), ("simvastatin", 40), ("lisinopril", 10)}
    assert p.allergies == ["penicillin"]
    assert {"hypertension", "GERD"} <= set(p.conditions)


def test_labs_match_p5_with_egfr_trend():
    labs = _profile().labs
    egfr = sorted((l for l in labs if l.test == "eGFR"), key=lambda l: l.date)
    assert [l.value for l in egfr] == [62, 48]
    assert (egfr[1].date - egfr[0].date).days > 300
    latest = {l.test: l.value for l in labs if l.date == date(2026, 10, 28)}
    assert latest == {"eGFR": 48, "potassium": 5.2, "ALT": 28, "CK": 110, "LDL": 142}


def test_no_pantoprazole_in_meds():
    # S6 no-extrapolation demo asks about pantoprazole as a *new* drug
    assert "pantoprazole" not in {m.ingredient for m in _profile().meds}


def test_vcf_agrees_with_profile_genotypes():
    v = _vcf()
    assert v["rs4244285"] == ("CYP2C19", "*2", "1/1")      # *2/*2
    assert v["rs4149056"] == ("SLCO1B1", "*5", "0/1")      # *1/*5
    assert v["rs2306283"][2] == "0/0"                      # 388A>G absent, so *5 not *15
    others = {rs: gt for rs, (_, _, gt) in v.items() if rs not in {"rs4244285", "rs4149056"}}
    assert set(others.values()) == {"0/0"}                 # CYP2C9, VKORC1 reference
    assert {g for g, _, _ in v.values()} == {"CYP2C19", "SLCO1B1", "CYP2C9", "VKORC1"}   # no CYP2D6 (D-021)
