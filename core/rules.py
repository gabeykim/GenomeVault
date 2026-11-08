"""M4 rules engine: one drug + the local profile -> exact-key Flags (PLAN F3, M4).

Everything runs on the device and reads only `data/rules/*.json`. Four engines:

- gene_drug   `GENE:phenotype|drug[|dose>Nmg]`, fires when the profile phenotype matches exactly.
- drug_drug   `a|b` (contracts.pair_key) against every other med in the profile.
- drug_lab    `drug|<lab><op><value>`, fires on the most recent result for that lab.
- class_rule  authored class pairs (I4), expanded to exact pair keys over listed members only.
- allergy     `allergy:<group>|drug`, fires when a profile allergy names an authored group (or alias)
              and the drug is a listed member; an allergy written as a member's own name matches
              only that ingredient (`allergy:amoxicillin|amoxicillin`). No cross-group inference.

A key that is not in a table produces no flag (I4: no extrapolation between drugs). Every flag comes
from a `curated` entry, so high-severity flags always have a curated source (I6). Flag ids are the
PLAN P5 finding ids from `flag_ids.json` (X1..X5); other keys carry their rule id.

Two guards from D-021: genes in `NOT_ASSESSED` (CYP2D6, SNP-uncallable) or with phenotype
`not_assessed` are never read by any rule; and pairs in `expected_combinations.json` (e.g.
`aspirin|clopidogrel`, DAPT after a stent) never become Flags; `expected_notes()` returns them as
informational notes instead.
"""
from __future__ import annotations

import functools
import json
import operator
import pathlib
from typing import Literal, Optional

from .contracts import Drug, Flag, Lab, Profile, pair_key

RULES_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "rules"
TABLES = ("gene_drug", "drug_drug", "drug_lab", "class_rules", "allergy")
NOT_ASSESSED = frozenset({"CYP2D6"})       # D-021: deletions/duplications not callable from SNPs
OPS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}


# --- tables ------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def tables() -> dict:
    """All rule tables plus the flag-id map, read once."""
    out = {name: json.loads((RULES_DIR / f"{name}.json").read_text()) for name in TABLES}
    out["flag_ids"] = json.loads((RULES_DIR / "flag_ids.json").read_text())["ids"]
    out["expected"] = json.loads((RULES_DIR / "expected_combinations.json").read_text())["combinations"]
    return out


def expected_keys() -> set[str]:
    """Pair keys that are expected therapy: never a Flag (D-021)."""
    return {c["key"] for c in tables()["expected"]}


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


def allergy_key(allergen: str, drug: str) -> str:
    return f"allergy:{allergen}|{drug}"


def allergy_rule_keys(rule: dict, groups: dict) -> dict[str, tuple[str, str]]:
    """Exact keys an allergy rule covers -> (allergen as keyed, ingredient): the group against each
    listed member, and each member against itself."""
    out = {}
    for m in groups[rule["group"]]["members"]:
        out[allergy_key(rule["group"], m)] = (rule["group"], m)
        out[allergy_key(m, m)] = (m, m)
    return out


def all_keys() -> set[str]:
    """Every exact key the local tables can produce (used by tests and the router's no_data path)."""
    t = tables()
    keys = {r["key"] for name in ("gene_drug", "drug_drug", "drug_lab") for r in t[name]["rules"]}
    for rule in t["class_rules"]["rules"]:
        keys |= set(class_rule_keys(rule, t["class_rules"]["classes"]))
    for rule in t["allergy"]["rules"]:
        keys |= set(allergy_rule_keys(rule, t["allergy"]["groups"]))
    return keys


# --- helpers -----------------------------------------------------------------------------------

def _phenotype(profile: Profile, gene: str) -> Optional[str]:
    """The phenotype a rule may read, or None for unassessed genes (D-021)."""
    ph = profile.phenotypes.get(gene)
    if gene in NOT_ASSESSED or ph in (None, "not_assessed"):
        return None
    return ph


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
        if r["drug"] != drug.ingredient or _phenotype(profile, r["gene"]) != r["phenotype"]:
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
        ph = _phenotype(profile, ctx["gene"]) if ctx else None
        if ph in (ctx or {}).get("phenotypes", []):
            evidence.append(f"{ctx['gene']} {ph.replace('_', ' ')}")
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


def _allergen(text: str) -> str:
    """An allergy as written on the record, in key form: 'Penicillin ' -> 'penicillin',
    'Sulfa drugs' -> 'sulfa drugs', 'penicillin v' -> 'penicillin_v'."""
    return " ".join(text.lower().replace("_", " ").split())


def _allergy(drug: Drug, profile: Profile) -> list[Flag]:
    groups = tables()["allergy"]["groups"]
    written = {_allergen(a): a.strip() for a in profile.allergies}
    out = []
    for r in tables()["allergy"]["rules"]:
        g = groups[r["group"]]
        if drug.ingredient not in g["members"]:
            continue
        names = {_allergen(r["group"]), *(_allergen(a) for a in g["aliases"])}
        hit = next((written[n] for n in written if n in names), None)
        if hit is not None:
            key = allergy_key(r["group"], drug.ingredient)
            evidence = [f"allergy on record: {hit}", f"{drug.ingredient.replace('_', ' ')} is {g['label']}"]
        elif _allergen(drug.ingredient) in written:
            key = allergy_key(drug.ingredient, drug.ingredient)
            evidence = [f"allergy on record: {written[_allergen(drug.ingredient)]}"]
        else:
            continue
        out.append(_flag(r, key, "allergy", evidence))
    return out


ENGINES = (_gene_drug, _drug_drug, _drug_lab, _class_rules, _allergy)


# --- API ---------------------------------------------------------------------------------------

def check(drug: Drug, profile: Profile) -> list[Flag]:
    """Flags for one drug against the profile (contract: CONTRACTS.md `rules.check`). Exact keys only."""
    drug = Drug(ingredient=drug.ingredient.strip().lower(), dose_mg=drug.dose_mg)
    expected = expected_keys()
    seen: dict[str, Flag] = {}
    for engine in ENGINES:
        for f in engine(drug, profile):
            if f.key not in expected:
                seen.setdefault(f.key, f)
    return list(seen.values())


def expected_notes(drug: Drug, profile: Profile) -> list[dict]:
    """Informational notes (not Flags) for expected combinations of `drug` with the med list, shown
    only when the profile has a listed condition. Each note: id, key, text, source (D-021)."""
    ing = drug.ingredient.strip().lower()
    others = set(_others(Drug(ingredient=ing), profile))
    out = []
    for c in tables()["expected"]:
        if ing not in c["drugs"] or not set(c["conditions"]) & set(profile.conditions):
            continue
        if any(d in others for d in c["drugs"] if d != ing):
            out.append({k: c[k] for k in ("id", "key", "text", "source")})
    return out


def expected_notes_all(profile: Profile) -> list[dict]:
    """Expected-combination notes across the whole med list, one per key."""
    seen: dict[str, dict] = {}
    for med in profile.meds:
        for n in expected_notes(med, profile):
            seen.setdefault(n["key"], n)
    return sorted(seen.values(), key=lambda n: n["id"])


def key_state(key: str) -> Literal["known", "none_listed", "no_data"]:
    """PLAN P6 answer state of one exact key in the local curated tables (I4, queue 8).

    `known`: the key has a curated entry (a rule, an expanded class rule, or an expected combination).
    `none_listed` would need a curated "listed as no interaction" entry; no such table is authored
    yet, so it is never returned today. Everything else is `no_data`: no rule, no flag, and no
    inference from a similar drug (e.g. `clopidogrel|pantoprazole` stays `no_data` although
    `clopidogrel|omeprazole` is known). Genes in NOT_ASSESSED are always `no_data`."""
    key = key.strip()
    if key.split(":", 1)[0] in NOT_ASSESSED:
        return "no_data"
    if key in all_keys() or key in expected_keys():
        return "known"
    return "no_data"


def no_data_keys(drug: Drug, profile: Profile) -> list[str]:
    """Drug-drug pair keys between `drug` and each other med in the profile that the local tables do
    not cover (state `no_data`). `check()` returns no flag for these; this is the marker the router
    and UI can use to say "no entry", never "no interaction" (I4, I7). Sorted, one per key."""
    ing = drug.ingredient.strip().lower()
    keys = {pair_key(ing, other) for other in _others(Drug(ingredient=ing), profile)}
    return sorted(k for k in keys if key_state(k) == "no_data")


def check_all(profile: Profile) -> list[Flag]:
    """Flags for every med in the profile, one per exact key (e.g. X2 is found from both sides)."""
    seen: dict[str, Flag] = {}
    for med in profile.meds:
        for f in check(med, profile):
            seen.setdefault(f.key, f)
    return sorted(seen.values(), key=lambda f: (f.id, f.key))
