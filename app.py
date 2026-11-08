"""GenomeVault app (Agent C, M10): FastAPI backend for the two-pane UI.

Runs on localhost and makes no network calls itself (I2). Any cloud traffic happens inside
core/cloud.py, behind router.route.

Each dependency is resolved once at startup: the real module is used as soon as it exists on
main (A at G1, B at G2, C's own merge.py), otherwise the stub from core/interfaces.py
(coord/CONTRACTS.md). /api/status reports which is which.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import interfaces
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


app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
