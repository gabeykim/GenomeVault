"""GenomeVault app (Agent C, M10): FastAPI backend for the two-pane UI.

Runs on localhost and makes no network calls itself (I2). Any cloud traffic happens inside
core/cloud.py, behind router.route.

Each dependency is resolved once at startup: the real module is used as soon as it exists on
main (A at G1, B at G2, C's own merge.py), otherwise the stub from core/interfaces.py
(coord/CONTRACTS.md). /api/status reports which is which.
"""
from __future__ import annotations

import html
import importlib
import importlib.util
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import actions, interfaces
from core.contracts import Answer, Drug, Fact, Flag, LedgerEntry, Profile

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
DEMO = os.environ.get("DEMO", "0") == "1"
DISCLAIMER = "Demo, not medical advice. All patient data is synthetic."


# --- stand-ins for contract functions that core/interfaces.py does not stub yet ---------------

class _MockLedger:
    """Stand-in for B's ledger until G2. Only used while core/ledger.py does not exist."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._lock = threading.Lock()

    def record(self, kind: str, bytes_out: int = 0, bucket_id: Optional[str] = None) -> None:
        with self._lock:
            self._entries.append(LedgerEntry(
                seq=len(self._entries) + 1, ts=datetime.now(timezone.utc),
                bucket_id=bucket_id, kind=kind, bytes_out=bytes_out))

    def feed(self, since: int) -> list[LedgerEntry]:
        with self._lock:
            return [e for e in self._entries if e.seq > since]


_mock_ledger = _MockLedger()
MOCK_BUCKET_BYTES = 8 * 180  # mock only: 8 generalized questions of ~180 bytes each


def _mock_to_ingredients(text: str) -> list[Drug]:
    """Stand-in for A's normalize.to_ingredients until G1: treats the text as an ingredient name."""
    name = text.strip().lower()
    return [Drug(ingredient=name)] if name else []


# --- module resolution -------------------------------------------------------------------------

MODES: dict[str, str] = {}


def _resolve(module: str, attr: str, fallback: Callable) -> Callable:
    """core.<module>.<attr> if that module exists, else the mock. A broken real module raises;
    it never silently falls back to the mock."""
    name = f"{module}.{attr}"
    if importlib.util.find_spec(f"core.{module}") is not None:
        MODES[name] = "real"
        return getattr(importlib.import_module(f"core.{module}"), attr)
    MODES[name] = "mock"
    return fallback


load_profile = _resolve("graph", "load_profile", interfaces.load_profile)
check = _resolve("rules", "check", interfaces.check)
to_ingredients = _resolve("normalize", "to_ingredients", _mock_to_ingredients)
route = _resolve("router", "route", interfaces.route)
personalize = _resolve("merge", "personalize", interfaces.personalize)
ledger_feed = _resolve("ledger", "feed", _mock_ledger.feed)
LEDGER_IS_MOCK = MODES["ledger.feed"] == "mock"


def _note(kind: str, bytes_out: int = 0, bucket_id: Optional[str] = None) -> None:
    """Record an event in the mock ledger. Once B's ledger is real, B writes every entry itself."""
    if LEDGER_IS_MOCK:
        _mock_ledger.record(kind, bytes_out, bucket_id)


# --- helpers -----------------------------------------------------------------------------------

def _flags_for(drugs: list[Drug], profile: Profile) -> list[Flag]:
    seen: dict[str, Flag] = {}
    for drug in drugs:
        for flag in check(drug, profile):
            seen.setdefault(flag.id, flag)
    return sorted(seen.values(), key=lambda f: f.id)


def tier_label(fact: Fact) -> str:
    """Trust-tier label shown next to every fact (I6)."""
    if fact.tier == "cloud":
        return "AI-summarized, verify"
    return f"Curated: {fact.source}"


# --- API ---------------------------------------------------------------------------------------

app = FastAPI(title="GenomeVault", docs_url=None, redoc_url=None)


_asked: deque[str] = deque(maxlen=10)   # recent questions, in memory only, for the visit summary


class CheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return {"demo": DEMO, "disclaimer": DISCLAIMER, "modules": MODES}


@app.get("/api/profile", response_model=Profile)
def profile() -> Profile:
    return load_profile()


@app.get("/api/flags")
def flags() -> dict:
    """Flags for the current medication list, all computed on device."""
    p = load_profile()
    result = _flags_for(p.meds, p)
    _note("local_only")
    return {"checked": [d.ingredient for d in p.meds], "flags": [f.model_dump() for f in result]}


@app.post("/api/check")
def check_drug(body: CheckIn) -> dict:
    """Check one typed drug name against the profile (F2 typed input, F3)."""
    p = load_profile()
    drugs = to_ingredients(body.text)
    result = _flags_for(drugs, p)
    _note("local_only")
    return {"input": body.text, "drugs": [d.model_dump() for d in drugs],
            "flags": [f.model_dump() for f in result]}


@app.post("/api/ask")
def ask(body: AskIn) -> dict:
    """Open question: router decides what (if anything) leaves; merge personalizes locally."""
    p = load_profile()
    current = _flags_for(p.meds, p)
    answer: Answer = route(body.question, current)
    _asked.append(body.question)
    if answer.sent_to_cloud:
        _note("bucket", MOCK_BUCKET_BYTES, "mock-bucket")
    else:
        _note("local_only")
    return {
        "state": answer.state,
        "text": personalize(answer, current, p),
        "facts": [{**f.model_dump(mode="json"), "label": tier_label(f)} for f in answer.facts],
        "sent_to_cloud": answer.sent_to_cloud,
    }


@app.get("/api/ledger")
def ledger(since: int = 0) -> dict:
    """Live outbound ledger (F5). The UI polls with the last seq it has."""
    everything = ledger_feed(0)
    return {
        "entries": [e.model_dump(mode="json") for e in everything if e.seq > since],
        "totals": {
            "count": len(everything),
            "bytes_out": sum(e.bytes_out for e in everything),
            "personal_fields_sent": sum(e.personal_fields_sent for e in everything),
        },
        "mock": LEDGER_IS_MOCK,
    }


# --- actions (F7): prepared on device, handed to the user; nothing is sent (I2) ----------------

def _current() -> tuple[list[Flag], Profile]:
    p = load_profile()
    return _flags_for(p.meds, p), p


@app.get("/api/actions/pharmacist")
def pharmacist() -> dict:
    flags_now, p = _current()
    return {"text": actions.pharmacist_draft(flags_now, p)}


@app.get("/api/actions/summary")
def summary() -> dict:
    flags_now, p = _current()
    s = actions.visit_summary(flags_now, p, list(_asked))
    return {**s, "text": actions.summary_text(s)}


@app.get("/api/actions/reminders")
def reminders() -> dict:
    flags_now, p = _current()
    return {"reminders": actions.reminders(flags_now, p)}


@app.get("/api/actions/reminders.ics")
def reminders_ics() -> Response:
    flags_now, p = _current()
    return Response(actions.reminders_ics(actions.reminders(flags_now, p)), media_type="text/calendar",
                    headers={"Content-Disposition": 'attachment; filename="genomevault-reminders.ics"'})


SUMMARY_CSS = """
:root { --paper:#fff; --ink:#0b0b0b; --mute:#6b6b67; --line:#c3c3be; }
* { box-sizing: border-box; }
body { margin: 0; background: #e1e1de; color: var(--ink); font: 13px/1.45 "Helvetica Neue", Helvetica, Arial, sans-serif; }
.page { max-width: 780px; margin: 24px auto; padding: 40px 48px; background: var(--paper); }
.top { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 8px solid var(--ink); padding-bottom: 10px; }
h1 { margin: 0; font-size: 34px; font-weight: 500; letter-spacing: -.04em; }
.meta { color: var(--mute); font-size: 12px; text-align: right; }
section { display: grid; grid-template-columns: 170px 1fr; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
h2 { margin: 0; font-size: 12px; font-weight: 400; color: var(--mute); }
ul { margin: 0; padding: 0; list-style: none; }
li { padding: 2px 0; }
.note { margin-top: 16px; color: var(--mute); font-size: 11.5px; }
.bar { max-width: 780px; margin: 16px auto 0; display: flex; justify-content: space-between; font-size: 12px; }
.bar a, .bar button { color: var(--ink); background: none; border: 1px solid var(--ink); padding: 6px 12px; font: inherit; cursor: pointer; text-decoration: none; }
@media print { body { background: #fff; } .bar { display: none; } .page { margin: 0; padding: 0; max-width: none; } }
@media (max-width: 640px) { .page { padding: 24px 16px; margin: 0; } section { grid-template-columns: 1fr; gap: 4px; } }
"""


@app.get("/summary", response_class=HTMLResponse, include_in_schema=False)
def summary_page() -> str:
    """Printable one-page visit summary. Self-contained: no external assets (I8)."""
    s = summary()
    esc = html.escape
    sections = "".join(
        f"<section><h2>{esc(sec['heading'])}</h2><ul>{''.join(f'<li>{esc(i)}</li>' for i in sec['items'])}</ul></section>"
        for sec in s["sections"])
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>Visit summary · GenomeVault</title><style>{SUMMARY_CSS}</style></head><body>"
            f"<div class='bar'><a href='/'>← Back to GenomeVault</a><button onclick='print()'>Print</button></div>"
            f"<main class='page'><div class='top'><h1>{esc(s['title'])}</h1>"
            f"<div class='meta'>Prepared {esc(s['prepared'])}<br>GenomeVault</div></div>"
            f"{sections}<p class='note'>{esc(s['note'])}</p></main></body></html>")


app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
