"""M4 rules engine: one drug + the local profile -> exact-key Flags (PLAN F3, M4).

Everything runs on the device and reads only `data/rules/*.json`. Four engines:

- gene_drug   `GENE:phenotype|drug[|dose>Nmg]`, fires when the profile phenotype matches exactly.
- drug_drug   `a|b` (contracts.pair_key) against every other med in the profile.
- drug_lab    `drug|<lab><op><value>`, fires on the most recent result for that lab.
- class_rule  authored class pairs (I4), expanded to exact pair keys over listed members only.

A key that is not in a table produces no flag (I4: no extrapolation between drugs). Every flag comes
from a `curated` entry, so high-severity flags always have a curated source (I6). Flag ids are the
PLAN P5 finding ids from `flag_ids.json` (X1..X5); other keys carry their rule id.
"""
from __future__ import annotations

import functools
import json
import operator
import pathlib
from typing import Optional

from .contracts import Drug, Flag, Lab, Profile, pair_key

RULES_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "rules"
TABLES = ("gene_drug", "drug_drug", "drug_lab", "class_rules")
OPS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}


# --- tables ------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def tables() -> dict:
    """All rule tables plus the flag-id map, read once."""
    out = {name: json.loads((RULES_DIR / f"{name}.json").read_text()) for name in TABLES}
    out["flag_ids"] = json.loads((RULES_DIR / "flag_ids.json").read_text())["ids"]
    return out


def _num(x: float) -> str:
    """Number as written in keys and evidence: 20 -> '20', 5.0 -> '5.0' stays as authored."""
    return str(x)


def gene_drug_key(gene: str, phenotype: str, drug: str, dose: Optional[dict] = None) -> str:
    key = f"{gene}:{phenotype}|{drug}"
    if dose:
        key += f"|dose{dose['op']}{_num(dose['mg'])}mg"
    return key


def drug_lab_key(drug: str, lab: str, op: str, value: float) -> str:
    return f"{drug}|{lab}{op}{_num(value)}"


def class_rule_keys(rule: dict, classes: dict) -> dict[str, tuple[str, str]]:
    """Exact pair keys a class rule covers -> (member of class 0, member of class 1)."""
    a, b = rule["classes"]
    out = {}
    for x in classes[a]["members"]:
        for y in classes[b]["members"]:
            if x != y:
                out[pair_key(x, y)] = (x, y)
    return out


def all_keys() -> set[str]:
    """Every exact key the local tables can produce (used by tests and the router's no_data path)."""
    t = tables()
    keys = {r["key"] for name in ("gene_drug", "drug_drug", "drug_lab") for r in t[name]["rules"]}
    for rule in t["class_rules"]["rules"]:
        keys |= set(class_rule_keys(rule, t["class_rules"]["classes"]))
    return keys


# --- helpers -----------------------------------------------------------------------------------

def _g(x: float) -> str:
    return f"{x:g}"


def _labs(profile: Profile, token: str) -> list[Lab]:
    """Results for one lab token (`egfr`, `potassium`), oldest first."""
    return sorted((lab for lab in profile.labs if lab.test.lower().replace(" ", "") == token),
                  key=lambda lab: lab.date)


def _lab_line(lab: Lab) -> str:
    line = f"{lab.test} {_g(lab.value)}"
    return line + " (older than 90 days)" if lab.stale else line


def _trend(profile: Profile, token: str) -> Optional[str]:
    labs = _labs(profile, token)
    if len(labs) < 2:
        return None
    return f"{labs[0].test} " + " -> ".join(_g(lab.value) for lab in labs)


def _context(profile: Profile, tokens: list[str]) -> list[str]:
    return [t for t in (_trend(profile, tok) for tok in tokens) if t]


def _dose(drug: Drug, profile: Profile) -> Optional[float]:
    """The checked dose, else the dose of the same ingredient already in the profile."""
    if drug.dose_mg is not None:
        return drug.dose_mg
    return next((m.dose_mg for m in profile.meds if m.ingredient == drug.ingredient and m.dose_mg is not None), None)


def _others(drug: Drug, profile: Profile) -> list[str]:
    seen: list[str] = []
    for m in profile.meds:
        ing = m.ingredient.lower()
        if ing != drug.ingredient and ing not in seen:
            seen.append(ing)
    return seen


def _flag(rule: dict, key: str, engine: str, evidence: list[str]) -> Flag:
    return Flag(id=tables()["flag_ids"].get(key, rule["id"]), key=key, severity=rule["severity"],
                engine=engine, evidence=evidence, needs_cloud=rule["needs_cloud"])


# --- engines -----------------------------------------------------------------------------------

def _gene_drug(drug: Drug, profile: Profile) -> list[Flag]:
    out = []
    for r in tables()["gene_drug"]["rules"]:
        if r["drug"] != drug.ingredient or profile.phenotypes.get(r["gene"]) != r["phenotype"]:
            continue
        evidence = [f"{r['gene']} {r['phenotype'].replace('_', ' ')}"]
        if r["dose"]:
            dose = _dose(drug, profile)
            if dose is None:      # unknown dose: still worth asking about (I7: prepare, never reassure)
                evidence.append(f"{drug.ingredient} dose not stated; applies at {r['dose']['op']}{_g(r['dose']['mg'])} mg")
            elif OPS[r["dose"]["op"]](dose, r["dose"]["mg"]):
                evidence.append(f"{drug.ingredient} {_g(dose)} mg")
            else:
                continue
        out.append(_flag(r, r["key"], "gene_drug", evidence))
    return out


def _drug_drug(drug: Drug, profile: Profile) -> list[Flag]:
    by_key = {r["key"]: r for r in tables()["drug_drug"]["rules"]}
    out = []
    for other in _others(drug, profile):
        r = by_key.get(pair_key(drug.ingredient, other))
        if r is None:
            continue
        evidence = list(r.get("evidence", []))
        ctx = r.get("context_gene")
        if ctx and profile.phenotypes.get(ctx["gene"]) in ctx["phenotypes"]:
            evidence.append(f"{ctx['gene']} {profile.phenotypes[ctx['gene']].replace('_', ' ')}")
        out.append(_flag(r, r["key"], "drug_drug", evidence))
    return out


def _drug_lab(drug: Drug, profile: Profile) -> list[Flag]:
    out = []
    for r in tables()["drug_lab"]["rules"]:
        if r["drug"] != drug.ingredient:
            continue
        labs = _labs(profile, r["lab"])
        if not labs or not OPS[r["op"]](labs[-1].value, r["value"]):
            continue
        evidence = [_lab_line(labs[-1])]
        evidence += [t for t in _context(profile, r.get("context_labs", [])) if t not in evidence]
        out.append(_flag(r, r["key"], "drug_lab", evidence))
    return out


def _class_rules(drug: Drug, profile: Profile) -> list[Flag]:
    t = tables()
    classes = t["class_rules"]["classes"]
    explicit = {r["key"] for r in t["drug_drug"]["rules"]}
    others = set(_others(drug, profile))
    out = []
    for r in t["class_rules"]["rules"]:
        for key, (x, y) in class_rule_keys(r, classes).items():
            if key in explicit or drug.ingredient not in (x, y):
                continue
            other = y if drug.ingredient == x else x
            if other not in others:
                continue
            a, b = r["classes"]
            evidence = [f"{x} is {classes[a]['label']}", f"{y} is {classes[b]['label']}"]
            evidence += _context(profile, r.get("context_labs", []))
            out.append(_flag(r, key, "class_rule", evidence))
    return out


ENGINES = (_gene_drug, _drug_drug, _drug_lab, _class_rules)


# --- API ---------------------------------------------------------------------------------------

def check(drug: Drug, profile: Profile) -> list[Flag]:
    """Flags for one drug against the profile (contract: CONTRACTS.md `rules.check`). Exact keys only."""
    drug = Drug(ingredient=drug.ingredient.strip().lower(), dose_mg=drug.dose_mg)
    seen: dict[str, Flag] = {}
    for engine in ENGINES:
        for f in engine(drug, profile):
            seen.setdefault(f.key, f)
    return list(seen.values())


def check_all(profile: Profile) -> list[Flag]:
    """Flags for every med in the profile, one per exact key (e.g. X2 is found from both sides)."""
    seen: dict[str, Flag] = {}
    for med in profile.meds:
        for f in check(med, profile):
            seen.setdefault(f.key, f)
    return sorted(seen.values(), key=lambda f: (f.id, f.key))
