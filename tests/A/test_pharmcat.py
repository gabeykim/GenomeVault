"""A stretch: PharmCAT path. Read a PharmCAT phenotype report next to our own VCF caller.

All reports here are SYNTHETIC (I1), shaped like PharmCAT 2.x ``*.phenotype.json``.
"""
import json

from core import ingest, rules
from core.contracts import Drug


def dip(a1, a2, *phenotypes, label=True):
    d = {"allele1": {"name": a1}, "allele2": {"name": a2}, "phenotypes": list(phenotypes)}
    if label:
        d["label"] = f"{a1}/{a2}"
    return d


def report(**genes):
    """gene -> list of diplotypes, wrapped as {"geneReports": {"CPIC": {...}}}."""
    return {"geneReports": {"CPIC": {g: {"geneSymbol": g, "recommendationDiplotypes": d}
                                     for g, d in genes.items()}}}


ALEX = report(
    CYP2C19=[dip("*2", "*2", "Poor Metabolizer")],
    SLCO1B1=[dip("*1", "*5", "Decreased Function")],
    CYP2C9=[dip("*1", "*1", "Normal Metabolizer")],
    CYP2D6=[dip("*1", "*1", "Normal Metabolizer")],
)


def test_alex_report_agrees_with_our_vcf_caller():
    p = ingest.ingest(pharmcat=ALEX)
    assert p.phenotypes == {
        "CYP2C19": "poor_metabolizer", "SLCO1B1": "decreased_function",
        "CYP2D6": "not_assessed", "CYP2C9": "normal_metabolizer",
        "VKORC1": "normal_sensitivity",  # not in the report: VCF call kept
    }
    assert p.genotypes["CYP2C19"] == "*2/*2"
    assert {"X1", "X2", "X3", "X4"} <= {f.id for f in rules.check_all(p)}


def test_cyp2d6_is_never_taken_from_pharmcat():
    # D-021: SNP data cannot call CYP2D6, even if a report claims a phenotype
    calls = ingest.read_pharmcat(report(CYP2D6=[dip("*4", "*4", "Poor Metabolizer")]))
    assert "CYP2D6" not in calls
    p = ingest.ingest(pharmcat=report(CYP2D6=[dip("*4", "*4", "Poor Metabolizer")]))
    assert p.phenotypes["CYP2D6"] == p.genotypes["CYP2D6"] == "not_assessed"


def test_ambiguous_or_unknown_calls_are_indeterminate():
    calls = ingest.read_pharmcat(report(
        CYP2C19=[dip("*1", "*2", "Intermediate Metabolizer"), dip("*2", "*17", "Intermediate Metabolizer")],
        CYP2C9=[dip("*1", "*2", "Likely Intermediate Metabolizer")],
        SLCO1B1=[dip("*1", "*99", "Indeterminate")],
        VKORC1=[dip("rs9923231 reference", "rs9923231 reference")],  # no phenotype given
    ))
    assert set(calls) == {"CYP2C19", "CYP2C9", "SLCO1B1", "VKORC1"}
    assert all(c == ("indeterminate", "indeterminate") for c in calls.values())


def test_disagreement_with_vcf_is_indeterminate_and_drops_the_flag():
    # VCF says CYP2C19 *2/*2 poor; a report saying normal must not silently clear X1 (I4)
    p = ingest.ingest(pharmcat=report(CYP2C19=[dip("*1", "*1", "Normal Metabolizer")]))
    assert p.phenotypes["CYP2C19"] == p.genotypes["CYP2C19"] == "indeterminate"
    ids = {f.id for f in rules.check(Drug(ingredient="clopidogrel"), p)}
    assert "X1" not in ids


def test_pharmcat_fills_a_gene_the_vcf_could_not_call(tmp_path):
    vcf = tmp_path / "missing.vcf"
    vcf.write_text("##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
                   "chr10\t94781859\trs4244285\tG\tA\t.\tPASS\t.\tGT\t./.\n")
    assert ingest.genotype_vcf(vcf)[1]["CYP2C19"] == "indeterminate"
    p = ingest.ingest(vcf=vcf, pharmcat=report(CYP2C19=[dip("*1", "*17", "Rapid Metabolizer")]))
    assert p.genotypes["CYP2C19"] == "*1/*17"
    assert p.phenotypes["CYP2C19"] == "rapid_metabolizer"


def test_label_falls_back_to_allele_names_and_reads_from_file(tmp_path):
    path = tmp_path / "alex.phenotype.json"
    path.write_text(json.dumps(report(SLCO1B1=[dip("*1", "*5", "Decreased Function", label=False)])))
    assert ingest.read_pharmcat(path) == {"SLCO1B1": ("*1/*5", "decreased_function")}


def test_gene_keyed_reports_and_cpic_precedence():
    flat = {"geneReports": {"CYP2C9": {"recommendationDiplotypes": [dip("*1", "*3", "Intermediate Metabolizer")]}}}
    assert ingest.read_pharmcat(flat) == {"CYP2C9": ("*1/*3", "intermediate_metabolizer")}
    two = {"geneReports": {
        "DPWG": {"CYP2C9": {"recommendationDiplotypes": [dip("*3", "*3", "Poor Metabolizer")]}},
        "CPIC": {"CYP2C9": {"recommendationDiplotypes": [dip("*1", "*1", "Normal Metabolizer")]}},
    }}
    assert ingest.read_pharmcat(two) == {"CYP2C9": ("*1/*1", "normal_metabolizer")}


def test_malformed_reports_yield_nothing():
    for bad in ({}, {"geneReports": []}, {"geneReports": {"CPIC": "x"}},
                {"geneReports": {"CPIC": {"NOTAGENE": {}}}}):
        assert ingest.read_pharmcat(bad) == {}


def test_default_ingest_unchanged_without_pharmcat():
    assert ingest.ingest().phenotypes == ingest.ingest(pharmcat=None).phenotypes
