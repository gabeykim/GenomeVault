"""D-021 / PLAN v1.2 P5 corrections: CYP2D6 not_assessed, aspirin|clopidogrel is expected DAPT (a note,
never a Flag), X1-X5 unchanged, VCF on GRCh38 and matched by rsID."""
import json
import pathlib

import pytest

from core import rules
from core.contracts import Drug, Profile

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def _alex() -> Profile:
    return Profile.model_validate_json((DATA / "alex_profile.json").read_text())


def _with_phenotype(gene: str, phenotype: str) -> Profile:
    p = _alex()
    ph = dict(p.phenotypes)
    ph[gene] = phenotype
    return p.model_copy(update={"phenotypes": ph})


def _vcf_rows() -> list[list[str]]:
    return [l.split("\t") for l in (DATA / "alex.vcf").read_text().splitlines() if l and not l.startswith("#")]


# --- CYP2D6 not_assessed -----------------------------------------------------------------------

def test_cyp2d6_is_not_assessed_in_profile():
    p = _alex()
    assert p.genotypes["CYP2D6"] == "not_assessed"
    assert p.phenotypes["CYP2D6"] == "not_assessed"


def test_no_rule_reads_cyp2d6():
    t = rules.tables()
    assert all(r["gene"] != "CYP2D6" for r in t["gene_drug"]["rules"])
    assert all((r.get("context_gene") or {}).get("gene") != "CYP2D6" for r in t["drug_drug"]["rules"])
    assert not any(k.startswith("CYP2D6") for k in rules.all_keys())


def test_engine_ignores_cyp2d6_even_if_a_rule_and_phenotype_exist(monkeypatch):
    # A CYP2D6 rule sneaking into the table must still never fire (D-021 guard in the engine).
    t = rules.tables()
    fake = dict(t["gene_drug"]["rules"][0], id="GD-999", key="CYP2D6:poor_metabolizer|codeine",
                gene="CYP2D6", phenotype="poor_metabolizer", drug="codeine", dose=None)
    monkeypatch.setitem(t["gene_drug"], "rules", t["gene_drug"]["rules"] + [fake])
    p = _with_phenotype("CYP2D6", "poor_metabolizer")
    assert rules.check(Drug(ingredient="codeine"), p) == []


def test_not_assessed_phenotype_matches_nothing():
    p = _with_phenotype("CYP2C19", "not_assessed")
    flags = {f.key: f for f in rules.check(Drug(ingredient="clopidogrel", dose_mg=75), p)}
    assert "CYP2C19:poor_metabolizer|clopidogrel" not in flags
    assert flags["clopidogrel|omeprazole"].evidence == ["omeprazole inhibits CYP2C19"]   # no phenotype line


# --- aspirin|clopidogrel is expected DAPT --------------------------------------------------------

def test_expected_combinations_schema():
    data = json.loads((DATA / "rules" / "expected_combinations.json").read_text())
    for c in data["combinations"]:
        assert c["key"] == "|".join(sorted(c["drugs"]))
        assert c["tier"] == "curated" and c["source"] and c["text"] and c["conditions"]
        assert "safe" not in c["text"].lower()          # I7
    assert "aspirin|clopidogrel" in {c["key"] for c in data["combinations"]}


def test_expected_keys_are_never_rule_keys():
    assert not (rules.expected_keys() & rules.all_keys())


@pytest.mark.parametrize("drug", ["aspirin", "clopidogrel"])
def test_aspirin_clopidogrel_gives_no_flag_but_a_note(drug):
    p = _alex()
    assert "aspirin|clopidogrel" not in {f.key for f in rules.check(Drug(ingredient=drug), p)}
    notes = rules.expected_notes(Drug(ingredient=drug), p)
    assert [n["key"] for n in notes] == ["aspirin|clopidogrel"]
    assert set(notes[0]) == {"id", "key", "text", "source"}


def test_note_needs_the_stent_context():
    p = _alex().model_copy(update={"conditions": ["hypertension"]})
    assert rules.expected_notes(Drug(ingredient="aspirin"), p) == []


def test_expected_notes_all_once():
    assert [n["id"] for n in rules.expected_notes_all(_alex())] == ["EX-001"]


def test_x1_to_x4_unchanged_and_x5_still_fires_for_ibuprofen():
    p = _alex()
    assert sorted({f.id for f in rules.check_all(p)}) == ["X1", "X2", "X3", "X4"]
    x5 = {f.key for f in rules.check(Drug(ingredient="ibuprofen", dose_mg=400), p) if f.id == "X5"}
    assert {"aspirin|ibuprofen", "clopidogrel|ibuprofen"} <= x5


# --- VCF: GRCh38 positions, rsID matching --------------------------------------------------------

def test_vcf_cyp2c19_positions_are_grch38_per_dbsnp():
    pos = {r[2]: (r[0], int(r[1])) for r in _vcf_rows()}
    assert pos["rs4244285"] == ("chr10", 94781859)
    assert pos["rs4986893"] == ("chr10", 94780653)
    assert pos["rs12248560"] == ("chr10", 94761900)
    assert ("chr10", 94775489) not in pos.values()      # that is rs17884712 (*9), not *3


def test_every_vcf_row_has_a_unique_rsid_and_no_cyp2d6():
    rows = _vcf_rows()
    assert all(r[2].startswith("rs") for r in rows)
    assert len({r[2] for r in rows}) == len(rows)
    assert not any("GENE=CYP2D6" in r[7] for r in rows)


def test_unverified_positions_are_marked_in_readme():
    readme = (DATA / "README.md").read_text()
    for rs in ("rs1799853", "rs1057910", "rs2306283", "rs4149056", "rs9923231"):
        line = next(l for l in readme.splitlines() if rs in l)
        assert "position unverified; matched by rsID" in line
