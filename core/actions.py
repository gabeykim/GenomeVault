"""Actions (Agent C, M9, F7): pharmacist draft, one-page visit summary, reminders.

Everything here is prepared on device and handed to the user; nothing is sent (I2). The user copies the
pharmacist draft, prints the summary, and imports reminders into their own calendar.

- I7: every line is phrased as a question or a prompt to talk to a professional, never as an instruction
  to start, stop or change a medication; all text passes merge.guard.
- Calendar files leave the device the moment a calendar syncs (iCloud, Google), so reminders_ics()
  carries no drug, gene, condition or lab value; the detail stays in the app.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .contracts import Flag, Profile
from .merge import _human, _key_parts, _lab_trend, guard

DEMO_NOTE = "Demo, not medical advice. All data is synthetic."
CLOSING = ("GenomeVault prepares you for this conversation; it never tells you to start or stop a "
           "medication.")
_ORDER = {"high": 0, "medium": 1, "low": 2}
CONDITION_NAMES = {
    "CAD_post_stent": "Coronary artery disease, post-stent",
    "hypertension": "High blood pressure",
    "hyperlipidemia": "High cholesterol",
    "GERD": "GERD (acid reflux)",
}


def _sorted(flags: list[Flag]) -> list[Flag]:
    return sorted(flags, key=lambda f: (_ORDER[f.severity], f.id))


def _dose(profile: Profile, drug: str) -> str:
    for m in profile.meds:
        if m.ingredient == drug:
            return f"{drug} {m.dose_mg:g} mg" if m.dose_mg is not None else drug
    return drug


def _gene_phrase(profile: Profile, gene: str) -> str:
    ph = profile.phenotypes.get(gene)
    gt = profile.genotypes.get(gene)
    return f"{gene} result is {_human(ph)}" + (f" ({gt})" if gt else "") if ph else f"{gene} result"


def _genes_in_evidence(flag: Flag, profile: Profile, exclude: list[str]) -> list[str]:
    text = " ".join(flag.evidence).lower()
    return [g for g in sorted(profile.phenotypes) if g not in exclude and g.lower() in text]


def question_for(flag: Flag, profile: Profile) -> str:
    """The flag as a question the user can ask, in their own terms (local only)."""
    drugs, genes, conds = _key_parts(flag.key)
    meds = [_dose(profile, d) for d in drugs]
    if flag.engine == "gene_drug" and genes:
        q = (f"My {_gene_phrase(profile, genes[0])}. Does that change how well {meds[0] if meds else 'my medicine'} "
             f"works for me, or its side effects?")
    elif flag.engine == "drug_drug" and len(meds) >= 2:
        extra = _genes_in_evidence(flag, profile, genes)
        why = f", given my {_gene_phrase(profile, extra[0])}" if extra else ""
        q = f"I take {meds[0]} and {meds[1]}. Is that combination something we should review{why}?"
    elif flag.engine == "drug_lab":
        labs = [c.split(">")[0].split("<")[0] for c in conds]
        labs += [l.test for l in profile.labs if l.test not in labs and l.test.lower() in " ".join(flag.evidence).lower()]
        trends = [t for t in (_lab_trend(profile, l) for l in dict.fromkeys(labs)) if t]
        q = (f"My recent labs show {' and '.join(trends) if trends else 'a change'}. "
             f"Does that matter for {meds[0] if meds else 'my medicines'}?")
    elif flag.engine == "allergy":
        allergy = profile.allergies[0] if profile.allergies else "an allergy"
        q = f"I'm allergic to {allergy}. Does {meds[0] if meds else 'this medicine'} relate to that allergy?"
    else:
        q = f"Should we review {', '.join(meds) if meds else flag.key} together?"
    return guard(q) or f"Could we review {flag.id}?"


# ---------- pharmacist draft ----------

def pharmacist_draft(flags: list[Flag], profile: Profile) -> str:
    """A message the user can copy and send to their pharmacist themselves."""
    meds = ", ".join(_dose(profile, m.ingredient) for m in profile.meds) or "no medications on record"
    lines = [
        "Hi,",
        "",
        "Before my next refill I'd like to go over a few things with you.",
        "",
        f"I currently take: {meds}.",
    ]
    if profile.allergies:
        lines.append(f"Allergies: {', '.join(profile.allergies)}.")
    lines.append("")
    if flags:
        lines.append("My genetic test and recent labs raised these questions:")
        for i, f in enumerate(_sorted(flags), 1):
            lines.append(f"{i}. {question_for(f, profile)}")
    else:
        lines.append("I'd like a general review of my medication list.")
    lines += [
        "",
        "I haven't changed anything I take. Could we go over these when you have a moment?",
        "",
        "Thank you,",
        "[Your name]",
        "",
        "Prepared on my own device with GenomeVault. " + DEMO_NOTE,
    ]
    return "\n".join(guard(l) if l else "" for l in lines)


# ---------- visit summary ----------

def visit_summary(flags: list[Flag], profile: Profile, questions: list[str] | None = None,
                  today: date | None = None) -> dict:
    """A one-page summary to print or show at a visit. Returns {title, prepared, note, sections}."""
    today = today or date.today()
    genes = []
    for g in sorted(profile.genotypes):
        ph = profile.phenotypes.get(g, "")
        notable = ph and not ph.startswith(("normal", "reference"))
        genes.append(f"{g} {profile.genotypes[g]}: {_human(ph)}" + (" (notable)" if notable else ""))
    labs = []
    for test in dict.fromkeys(l.test for l in profile.labs):
        rows = sorted((l for l in profile.labs if l.test == test), key=lambda l: l.date)
        latest = rows[-1]
        trend = _lab_trend(profile, test)
        stale = " (older than 90 days)" if latest.stale else ""
        labs.append(f"{trend}, {latest.date.isoformat()}{stale}")

    sections = [
        {"heading": "Current medications",
         "items": [_dose(profile, m.ingredient) for m in profile.meds] or ["None on record"]},
        {"heading": "Conditions and allergies",
         "items": [CONDITION_NAMES.get(c, _human(c)) for c in profile.conditions]
                  + [f"Allergy: {a}" for a in profile.allergies]},
        {"heading": "Pharmacogenomic results", "items": genes},
        {"heading": "Recent labs", "items": labs},
        {"heading": "To discuss",
         "items": [f"{f.id} ({f.severity}): {question_for(f, profile)}" for f in _sorted(flags)]
                  or ["No flags from the local tables."]},
    ]
    asked = [guard(q) for q in (questions or []) if guard(q)]
    if asked:
        sections.append({"heading": "Questions I asked GenomeVault", "items": asked})
    return {"title": "Visit summary", "prepared": today.isoformat(), "note": f"{DEMO_NOTE} {CLOSING}",
            "sections": sections}


def summary_text(summary: dict) -> str:
    out = [f"{summary['title']} · prepared {summary['prepared']}", ""]
    for s in summary["sections"]:
        out.append(s["heading"])
        out += [f"- {i}" for i in s["items"]]
        out.append("")
    out.append(summary["note"])
    return "\n".join(out)


# ---------- reminders ----------

def reminders(flags: list[Flag], profile: Profile, today: date | None = None) -> list[dict]:
    """Reminders to talk to someone, never to take, stop or change a medicine.
    Each: {id, due (ISO date), title, detail (on-device only), flags}."""
    today = today or date.today()
    out: list[dict] = []
    high = [f.id for f in _sorted(flags) if f.severity == "high"]
    if high:
        out.append({"id": "r-pharmacist", "due": (today + timedelta(days=1)).isoformat(),
                    "title": "Call your pharmacist",
                    "detail": f"Go over {', '.join(high)} using the pharmacist draft.", "flags": high})
    lab_flags = [f for f in _sorted(flags) if f.engine == "drug_lab"]
    if lab_flags:
        tests = []
        for f in lab_flags:
            _, _, conds = _key_parts(f.key)
            tests += [c.split(">")[0].split("<")[0] for c in conds]
            tests += [l.test for l in profile.labs if l.test.lower() in " ".join(f.evidence).lower()]
        tests = list(dict.fromkeys(tests))
        out.append({"id": "r-labs", "due": (today + timedelta(days=3)).isoformat(),
                    "title": "Ask about your recent labs",
                    "detail": f"Ask your doctor whether your {' and '.join(tests)} should be rechecked, and when.",
                    "flags": [f.id for f in lab_flags]})
    stale = sorted({l.test for l in profile.labs if l.stale})
    if stale:
        out.append({"id": "r-stale", "due": (today + timedelta(days=7)).isoformat(),
                    "title": "Ask whether old labs need updating",
                    "detail": f"Your {', '.join(stale)} result is older than 90 days.", "flags": []})
    if flags:
        out.append({"id": "r-visit", "due": (today + timedelta(days=7)).isoformat(),
                    "title": "Bring your visit summary to your next appointment",
                    "detail": "Print the one-page summary or show it on your phone.",
                    "flags": [f.id for f in _sorted(flags)]})
    for r in out:
        r["title"], r["detail"] = guard(r["title"]), guard(r["detail"])
    return out


def _ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def reminders_ics(items: list[dict], now: datetime | None = None) -> str:
    """iCalendar file for the user's own calendar. Generic text only: calendars sync to the cloud."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GenomeVault//demo//EN", "CALSCALE:GREGORIAN"]
    for r in items:
        day = r["due"].replace("-", "")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{r['id']}-{day}@genomevault.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day}",
            f"SUMMARY:{_ics_escape('GenomeVault: ' + r['title'])}",
            f"DESCRIPTION:{_ics_escape('Open GenomeVault on your device for the details.')}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
