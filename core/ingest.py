"""M1 ingest: VCF + records -> Profile (PLAN F1, P5, D-021). Local only, no network (I2).

Genotypes are matched by rsID (the VCF ``ID`` column), never by position, against
``data/pgx_alleles.json``; the VCF's own INFO/GENE and INFO/ALLELE are ignored. An rsID the file
does not list is reference. A gene whose call is missing (``./.``), has a REF/ALT mismatch, a
multi-allelic ALT, or more than two variant alleles comes out ``indeterminate``, which no rule
key uses, so it can never produce a flag (I4). CYP2D6 is always ``not_assessed`` (D-021).
"""
from __future__ import annotations

import functools
import json
import pathlib
from typing import Optional

from .contracts import Profile

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
VCF = DATA / "alex.vcf"
RECORDS = DATA / "alex_profile.json"
INDETERMINATE = "indeterminate"
NOT_ASSESSED = "not_assessed"


@functools.lru_cache(maxsize=1)
def table() -> dict:
    return json.loads((DATA / "pgx_alleles.json").read_text())


# --- VCF -----------------------------------------------------------------------------------------

def _alt_copies(gt: str, alt: str) -> Optional[int]:
    """Copies of ALT allele 1 in a diploid GT (``0/1``, ``1|1``...); None if uncallable."""
    parts = gt.replace("|", "/").split("/")
    if len(parts) != 2 or "." in parts or "," in alt:
        return None
    if any(p not in ("0", "1") for p in parts):
        return None
    return parts.count("1")


def parse_vcf(text: str) -> dict[str, Optional[int]]:
    """rsID -> ALT copies (0-2), or None if the call is unusable. Only rsIDs in the table count."""
    variants = table()["variants"]
    calls: dict[str, Optional[int]] = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 10:
            continue
        rs_ids = cols[2].split(";")
        fmt = cols[8].split(":")
        if "GT" not in fmt:
            continue
        fmt_idx = fmt.index("GT")
        sample = cols[9].split(":")
        gt = sample[fmt_idx] if fmt_idx < len(sample) else "./."
        for rs in rs_ids:
            v = variants.get(rs)
            if v is None:
                continue
            if cols[3].upper() != v["ref"] or cols[4].upper() != v["alt"]:
                calls[rs] = None                      # strand/build mismatch: don't guess
            else:
                calls[rs] = _alt_copies(gt, cols[4])
    return calls


# --- star alleles and phenotypes ----------------------------------------------------------------

def _diplotype(gene: str, copies: dict[str, int]) -> str:
    t = table()
    if gene in t["genotype_names"]:                    # single-SNP genes (VKORC1)
        (n,) = copies.values() or (0,)
        return t["genotype_names"][gene].get(str(n), INDETERMINATE)
    copies = {a: n for a, n in copies.items() if n}
    for hap, parts in t["haplotypes"].get(gene, {}).items():
        if all(copies.get(p, 0) for p in parts):
            if all(copies[p] == 1 for p in parts) and len(copies) == len(parts):
                # unphased double het: cis (*1/hap) or trans (a/b) cannot be told apart
                return f"*1/{hap} or {'/'.join(parts)}"
            n = min(copies[p] for p in parts)
            for p in parts:
                copies[p] -= n
            copies = {a: c for a, c in copies.items() if c}
            copies[hap] = n
    alleles = [a for a, n in copies.items() for _ in range(n)]
    if len(alleles) > 2:
        return INDETERMINATE
    alleles += ["*1"] * (2 - len(alleles))
    order = t["allele_order"].get(gene, [])
    alleles.sort(key=lambda a: order.index(a) if a in order else len(order))
    return "/".join(alleles)


def call_genes(calls: dict[str, Optional[int]]) -> tuple[dict[str, str], dict[str, str]]:
    """rsID calls -> (genotypes, phenotypes) for every gene in the table (PLAN P5: 5 genes)."""
    t = table()
    genotypes: dict[str, str] = {}
    phenotypes: dict[str, str] = {}
    for gene in t["genes"]:
        if gene in t["not_assessed"]:
            genotypes[gene] = phenotypes[gene] = NOT_ASSESSED
            continue
        copies: dict[str, int] = {}
        bad = False
        for rs, v in t["variants"].items():
            if v["gene"] != gene:
                continue
            n = calls.get(rs, 0)                       # unlisted rsID = reference
            if n is None:
                bad = True
            else:
                copies[v["allele"]] = n
        dip = INDETERMINATE if bad else _diplotype(gene, copies)
        genotypes[gene] = dip
        phenotypes[gene] = t["phenotypes"].get(gene, {}).get(dip, INDETERMINATE)
    return genotypes, phenotypes


def genotype_vcf(path: pathlib.Path | str = VCF) -> tuple[dict[str, str], dict[str, str]]:
    return call_genes(parse_vcf(pathlib.Path(path).read_text()))


# --- PharmCAT path (BRIEF A stretch) ------------------------------------------------------------
# PharmCAT is a separate Java tool the user runs on their own machine; we only read the
# ``*.phenotype.json`` it writes (stdlib json, no new dependency, no network: I2). Its calls are
# accepted only when they are unambiguous and use a phenotype our own table already knows.
# Anything else (several diplotypes, "Likely ...", "Indeterminate", "n/a", an unknown term, or a
# phenotype that disagrees with our VCF call) comes out ``indeterminate``, so it can never produce
# a flag (I4). CYP2D6 stays ``not_assessed`` whatever PharmCAT says (D-021).

def _snake(term: str) -> str:
    return "_".join(term.strip().lower().replace("-", " ").split())


def _gene_reports(report: dict) -> dict[str, dict]:
    """gene -> PharmCAT gene report. Accepts ``geneReports`` keyed by source (``{"CPIC": {...}}``,
    PharmCAT 2.x) or directly by gene. CPIC wins over other sources for the same gene."""
    reports = report.get("geneReports", {})
    if not isinstance(reports, dict):
        return {}
    genes = set(table()["genes"])
    if any(k in genes for k in reports):
        return {g: r for g, r in reports.items() if g in genes and isinstance(r, dict)}
    out: dict[str, dict] = {}
    for source in sorted(reports, key=lambda s: s != "CPIC"):
        by_gene = reports[source]
        if not isinstance(by_gene, dict):
            continue
        for g, r in by_gene.items():
            if g in genes and isinstance(r, dict):
                out.setdefault(g, r)
    return out


def _pharmcat_call(gene: str, rep: dict) -> tuple[str, str]:
    """(diplotype, phenotype) for one gene report; indeterminate unless exactly one known call."""
    dips = rep.get("recommendationDiplotypes") or rep.get("sourceDiplotypes") or []
    if len(dips) != 1 or not isinstance(dips[0], dict):
        return INDETERMINATE, INDETERMINATE
    d = dips[0]
    phs = d.get("phenotypes") or []
    known = set(table()["phenotypes"].get(gene, {}).values())
    ph = _snake(phs[0]) if len(phs) == 1 and isinstance(phs[0], str) else INDETERMINATE
    if ph not in known:
        return INDETERMINATE, INDETERMINATE
    label = d.get("label")
    if not isinstance(label, str) or not label.strip():
        names = [(d.get(k) or {}).get("name") for k in ("allele1", "allele2")]
        label = "/".join(n for n in names if isinstance(n, str)) or INDETERMINATE
    return label.strip(), ph


def read_pharmcat(report: dict | pathlib.Path | str) -> dict[str, tuple[str, str]]:
    """gene -> (diplotype, phenotype) for the table's genes that a PharmCAT phenotype report
    covers. Genes it does not mention are left out (the VCF caller keeps them)."""
    if not isinstance(report, dict):
        report = json.loads(pathlib.Path(report).read_text())
    calls = {}
    for gene, rep in _gene_reports(report).items():
        if gene in table()["not_assessed"]:
            continue                                   # D-021: never taken from PharmCAT
        calls[gene] = _pharmcat_call(gene, rep)
    return calls


def merge_pharmcat(genotypes: dict[str, str], phenotypes: dict[str, str],
                   pharmcat: dict[str, tuple[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    """Overlay PharmCAT calls on VCF calls. Where both give a phenotype and they differ, the gene
    is ``indeterminate``: we don't pick a side (I4)."""
    genotypes, phenotypes = dict(genotypes), dict(phenotypes)
    for gene, (dip, ph) in pharmcat.items():
        ours = phenotypes.get(gene, INDETERMINATE)
        if ph == INDETERMINATE or (ours not in (INDETERMINATE, NOT_ASSESSED) and ours != ph):
            genotypes[gene] = phenotypes[gene] = INDETERMINATE
        else:
            genotypes[gene], phenotypes[gene] = dip, ph
    return genotypes, phenotypes


# --- records + VCF -> Profile -------------------------------------------------------------------

def ingest(vcf: pathlib.Path | str = VCF, records: pathlib.Path | str = RECORDS,
           pharmcat: Optional[dict | pathlib.Path | str] = None) -> Profile:
    """Profile from a VCF (genotypes, phenotypes) plus a records file (meds, conditions, allergies,
    labs). Any genotypes/phenotypes in the records file are ignored: the VCF is the source. An
    optional PharmCAT phenotype report is overlaid gene by gene (see ``merge_pharmcat``)."""
    rec = json.loads(pathlib.Path(records).read_text())
    genotypes, phenotypes = genotype_vcf(vcf)
    if pharmcat is not None:
        genotypes, phenotypes = merge_pharmcat(genotypes, phenotypes, read_pharmcat(pharmcat))
    return Profile(genotypes=genotypes, phenotypes=phenotypes,
                   meds=rec.get("meds", []), conditions=rec.get("conditions", []),
                   allergies=rec.get("allergies", []), labs=rec.get("labs", []))
