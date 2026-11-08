"""A queue 5: ingest (VCF -> star alleles -> phenotypes, 5 genes) and graph (SQLite, stale labs)."""
import json
import pathlib
from datetime import date

import pytest

from core import graph, ingest, rules
from core.contracts import Drug, Profile

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
TODAY = date(2026, 11, 8)
HEADER = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
ROW = {  # rsID -> (chrom, pos, ref, alt) as in data/alex.vcf
    "rs12248560": ("chr10", 94761900, "C", "T"), "rs4986893": ("chr10", 94780653, "G", "A"),
    "rs4244285": ("chr10", 94781859, "G", "A"), "rs1799853": ("chr10", 94942290, "C", "T"),
    "rs1057910": ("chr10", 94981296, "A", "C"), "rs2306283": ("chr12", 21176804, "A", "G"),
    "rs4149056": ("chr12", 21178615, "T", "C"), "rs9923231": ("chr16", 31096368, "C", "T"),
}


def vcf(**gts) -> str:
    lines = []
    for rs, gt in gts.items():
        chrom, pos, ref, alt = ROW[rs]
        lines.append(f"{chrom}\t{pos}\t{rs}\t{ref}\t{alt}\t.\tPASS\t.\tGT\t{gt}")
    return HEADER + "\n".join(lines) + "\n"


def call(**gts):
    return ingest.call_genes(ingest.parse_vcf(vcf(**gts)))


def _json_profile() -> Profile:
    return Profile.model_validate_json((DATA / "alex_profile.json").read_text())


# --- ingest ----------------------------------------------------------------------------------

def test_alex_vcf_reproduces_p5_genotypes_and_phenotypes():
    genotypes, phenotypes = ingest.genotype_vcf()
    p = _json_profile()
    assert genotypes == p.genotypes
    assert phenotypes == p.phenotypes
    assert set(genotypes) == {"CYP2C19", "SLCO1B1", "CYP2D6", "CYP2C9", "VKORC1"}


def test_cyp2d6_always_not_assessed():
    g, ph = call()
    assert g["CYP2D6"] == ph["CYP2D6"] == "not_assessed"


@pytest.mark.parametrize("gts,dip,ph", [
    ({}, "*1/*1", "normal_metabolizer"),
    ({"rs4244285": "0/1"}, "*1/*2", "intermediate_metabolizer"),
    ({"rs4244285": "1|1"}, "*2/*2", "poor_metabolizer"),
    ({"rs4244285": "0/1", "rs4986893": "0/1"}, "*2/*3", "poor_metabolizer"),
    ({"rs12248560": "0/1"}, "*1/*17", "rapid_metabolizer"),
    ({"rs12248560": "1/1"}, "*17/*17", "ultrarapid_metabolizer"),
    ({"rs4244285": "0/1", "rs12248560": "0/1"}, "*2/*17", "intermediate_metabolizer"),
    ({"rs4244285": "1/1", "rs12248560": "0/1"}, "indeterminate", "indeterminate"),   # 3 alleles
])
def test_cyp2c19_calls(gts, dip, ph):
    g, p = call(**gts)
    assert (g["CYP2C19"], p["CYP2C19"]) == (dip, ph)


@pytest.mark.parametrize("gts,dip,ph", [
    ({"rs1799853": "0/1"}, "*1/*2", "intermediate_metabolizer"),
    ({"rs1799853": "0/1", "rs1057910": "0/1"}, "*2/*3", "poor_metabolizer"),
    ({"rs1057910": "1/1"}, "*3/*3", "poor_metabolizer"),
])
def test_cyp2c9_calls(gts, dip, ph):
    g, p = call(**gts)
    assert (g["CYP2C9"], p["CYP2C9"]) == (dip, ph)


@pytest.mark.parametrize("gts,dip,ph", [
    ({"rs4149056": "0/1"}, "*1/*5", "decreased_function"),
    ({"rs4149056": "1/1"}, "*5/*5", "poor_function"),
    ({"rs2306283": "0/1"}, "*1/*1B", "normal_function"),
    ({"rs2306283": "1/1", "rs4149056": "1/1"}, "*15/*15", "poor_function"),
    ({"rs2306283": "1/1", "rs4149056": "0/1"}, "*1B/*15", "decreased_function"),
    ({"rs2306283": "0/1", "rs4149056": "1/1"}, "*5/*15", "poor_function"),
    ({"rs2306283": "0/1", "rs4149056": "0/1"}, "*1/*15 or *1B/*5", "decreased_function"),  # unphased
])
def test_slco1b1_calls(gts, dip, ph):
    g, p = call(**gts)
    assert (g["SLCO1B1"], p["SLCO1B1"]) == (dip, ph)


@pytest.mark.parametrize("gt,dip,ph", [
    ("0/0", "reference", "normal_sensitivity"),
    ("0/1", "-1639G/A", "increased_sensitivity"),
    ("1/1", "-1639A/A", "high_sensitivity"),
])
def test_vkorc1_calls(gt, dip, ph):
    g, p = call(rs9923231=gt)
    assert (g["VKORC1"], p["VKORC1"]) == (dip, ph)


def test_missing_call_is_indeterminate_not_reference():
    g, p = call(rs4244285="./.")
    assert g["CYP2C19"] == p["CYP2C19"] == "indeterminate"


def test_matched_by_rsid_not_position_and_ref_alt_checked():
    # right position, wrong rsID: ignored (gene stays reference)
    moved = HEADER + "chr10\t94781859\trs999\tG\tA\t.\tPASS\t.\tGT\t1/1\n"
    assert ingest.call_genes(ingest.parse_vcf(moved))[0]["CYP2C19"] == "*1/*1"
    # right rsID, REF/ALT swapped (strand/build mismatch): don't guess
    flipped = HEADER + "chr10\t94781859\trs4244285\tA\tG\t.\tPASS\t.\tGT\t0/0\n"
    assert ingest.call_genes(ingest.parse_vcf(flipped))[1]["CYP2C19"] == "indeterminate"


def test_vcf_info_tags_are_ignored():
    lying = HEADER + "chr10\t94781859\trs4244285\tG\tA\t.\tPASS\tGENE=CYP2D6;ALLELE=*4\tGT:DP\t1/1:30\n"
    g, p = ingest.call_genes(ingest.parse_vcf(lying))
    assert g["CYP2C19"] == "*2/*2" and g["CYP2D6"] == "not_assessed"


def test_ingest_takes_records_but_genotypes_from_vcf(tmp_path):
    rec = json.loads((DATA / "alex_profile.json").read_text())
    rec["genotypes"] = {"CYP2C19": "*1/*1"}
    rec["phenotypes"] = {"CYP2C19": "normal_metabolizer"}
    (tmp_path / "r.json").write_text(json.dumps(rec))
    p = ingest.ingest(records=tmp_path / "r.json")
    assert p.phenotypes["CYP2C19"] == "poor_metabolizer"
    assert p.meds == _json_profile().meds


# --- graph -----------------------------------------------------------------------------------

def test_load_profile_matches_data_and_marks_stale_labs():
    p = graph.load_profile(on=TODAY)
    ref = _json_profile()
    assert p.genotypes == ref.genotypes and p.phenotypes == ref.phenotypes
    assert p.meds == ref.meds and p.conditions == ref.conditions and p.allergies == ref.allergies
    stale = {(l.test, l.date.isoformat()) for l in p.labs if l.stale}
    assert stale == {("eGFR", "2025-10-20")}
    assert len(p.labs) == len(ref.labs)


def test_stale_boundary_is_more_than_90_days():
    assert not graph.is_stale(date(2026, 8, 10), TODAY)     # exactly 90 days
    assert graph.is_stale(date(2026, 8, 9), TODAY)          # 91 days


def test_gv_today_pins_the_date(monkeypatch):
    monkeypatch.setenv("GV_TODAY", "2027-06-01")
    assert all(l.stale for l in graph.load_profile().labs)
    monkeypatch.setenv("GV_TODAY", "2026-11-08")
    assert sum(l.stale for l in graph.load_profile().labs) == 1


def test_sqlite_file_persists_and_is_reread(tmp_path, monkeypatch):
    db = tmp_path / "graph.db"
    monkeypatch.setenv("GV_GRAPH_DB", str(db))
    first = graph.load_profile(on=TODAY)
    assert db.exists()
    conn = graph.sqlite3.connect(db)
    conn.execute("DELETE FROM med WHERE ingredient = 'lisinopril'")
    conn.commit()
    conn.close()
    second = graph.load_profile(on=TODAY)                  # read from file, not re-ingested
    assert "lisinopril" in {m.ingredient for m in first.meds}
    assert "lisinopril" not in {m.ingredient for m in second.meds}


def test_x1_to_x4_fire_from_the_graph():
    p = graph.load_profile(on=TODAY)
    ids = {f.id for f in rules.check_all(p)}
    assert {"X1", "X2", "X3", "X4"} <= ids
    assert {f.id for f in rules.check(Drug(ingredient="ibuprofen"), p)} == {"X5"}


def test_no_rule_key_uses_ingest_only_vocabulary():
    # phenotype words ingest can emit but rules never read must not create keys (I4)
    keys = rules.all_keys()
    for word in ("indeterminate", "not_assessed"):
        assert not any(f":{word}|" in k for k in keys)
