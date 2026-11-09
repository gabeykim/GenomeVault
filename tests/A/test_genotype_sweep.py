"""End-to-end genotype sweep: every SNP genotype combination the allele table can see goes through
ingest (VCF -> phenotype) and then rules.check (PLAN F1, F3, M1, M4, I4).

Checks that (1) ingest only ever emits a phenotype from its own table or ``indeterminate``, (2) no
rule reads a phenotype ingest can never produce (a dead rule would silently never fire), and
(3) for every swept genotype a gene-drug flag fires exactly when the rule's phenotype (and dose
band) matches, never for ``indeterminate``.
"""
import itertools

import pytest

from core import ingest, rules
from core.contracts import Drug, Profile
from tests.A.test_ingest_graph import vcf

GT = {0: "0/0", 1: "0/1", 2: "1/1"}


def _variants_by_gene() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for rs, v in ingest.table()["variants"].items():
        out.setdefault(v["gene"], []).append(rs)
    return out


def _sweep(gene: str):
    """(genotypes dict, diplotype, phenotype) for every 0/1/2-copy combination of a gene's rsIDs."""
    rs_ids = _variants_by_gene()[gene]
    for copies in itertools.product((0, 1, 2), repeat=len(rs_ids)):
        gts = {rs: GT[n] for rs, n in zip(rs_ids, copies)}
        g, ph = ingest.call_genes(ingest.parse_vcf(vcf(**gts)))
        yield gts, g[gene], ph[gene]


SWEPT = {gene: list(_sweep(gene)) for gene in _variants_by_gene()}


def _rule_phenotypes() -> set[tuple[str, str]]:
    t = rules.tables()
    out = {(r["gene"], r["phenotype"]) for r in t["gene_drug"]["rules"]}
    for r in t["drug_drug"]["rules"]:
        ctx = r.get("context_gene")
        if ctx:
            out |= {(ctx["gene"], p) for p in ctx["phenotypes"]}
    return out


def test_sweep_covers_every_assessed_gene():
    t = ingest.table()
    assert set(SWEPT) == set(t["genes"]) - set(t["not_assessed"])
    assert len(SWEPT["CYP2C19"]) == 27


@pytest.mark.parametrize("gene", sorted(SWEPT))
def test_ingest_emits_only_table_phenotypes_or_indeterminate(gene):
    known = set(ingest.table()["phenotypes"][gene].values())
    for gts, dip, ph in SWEPT[gene]:
        assert ph in known | {ingest.INDETERMINATE}, (gts, dip, ph)
        if dip == ingest.INDETERMINATE:
            assert ph == ingest.INDETERMINATE, gts


@pytest.mark.parametrize("gene", sorted(SWEPT))
def test_more_than_two_variant_alleles_is_indeterminate(gene):
    # e.g. *2/*2 plus *17: three variant alleles in a diploid call is not a real diplotype
    for gts, dip, ph in SWEPT[gene]:
        n_alt = sum(g.count("1") for g in gts.values())
        if gene != "SLCO1B1" and n_alt > 2:            # SLCO1B1 *15 = *1B + *5 on one strand
            assert ph == ingest.INDETERMINATE, gts


@pytest.mark.parametrize("gene,phenotype", sorted(_rule_phenotypes()))
def test_every_rule_phenotype_is_reachable_from_a_vcf(gene, phenotype):
    assert phenotype in {ph for _, _, ph in SWEPT[gene]}, f"dead rule: {gene}:{phenotype}"


def _profile(gene: str, phenotype: str) -> Profile:
    t = ingest.table()
    phs = {g: ("not_assessed" if g in t["not_assessed"] else "normal_metabolizer") for g in t["genes"]}
    phs[gene] = phenotype
    return Profile(genotypes={}, phenotypes=phs, meds=[], conditions=[], allergies=[], labs=[])


def _expected(gene: str, phenotype: str, drug: str, dose: float) -> set[str]:
    out = set()
    for r in rules.tables()["gene_drug"]["rules"]:
        if (r["gene"], r["phenotype"], r["drug"]) != (gene, phenotype, drug):
            continue
        if r["dose"] and not rules.OPS[r["dose"]["op"]](dose, r["dose"]["mg"]):
            continue
        out.add(r["key"])
    return out


GENE_DRUGS = sorted({(r["gene"], r["drug"]) for r in rules.tables()["gene_drug"]["rules"]})


@pytest.mark.parametrize("gene,drug", GENE_DRUGS)
@pytest.mark.parametrize("dose", [10.0, 40.0])
def test_gene_drug_flag_fires_exactly_for_its_phenotype(gene, drug, dose):
    fired_for = set()
    for gts, dip, ph in SWEPT[gene]:
        flags = rules.check(Drug(ingredient=drug, dose_mg=dose), _profile(gene, ph))
        got = {f.key for f in flags if f.engine == "gene_drug"}
        assert got == _expected(gene, ph, drug, dose), (gts, dip, ph)
        if ph == ingest.INDETERMINATE:
            assert not got, gts                         # I4: no call, no flag
        if got:
            fired_for.add(ph)
    rule_phs = {r["phenotype"] for r in rules.tables()["gene_drug"]["rules"]
                if (r["gene"], r["drug"]) == (gene, drug)}
    assert fired_for <= rule_phs


def test_normal_metabolizer_on_clopidogrel_gets_no_gene_flag():
    flags = rules.check(Drug(ingredient="clopidogrel", dose_mg=75), _profile("CYP2C19", "normal_metabolizer"))
    assert not [f for f in flags if f.engine == "gene_drug"]
