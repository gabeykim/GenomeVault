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
from contextlib import asynccontextmanager
import importlib.util
import os
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import actions, interfaces, merge
from core.contracts import Answer, Drug, Fact, Flag, LedgerEntry, Profile

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
PHONE_DIR = ROOT / "phone"
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
from_image = _resolve("capture", "from_image", interfaces.from_image)   # A, D-020: label photo -> drugs
route = _resolve("router", "route", interfaces.route)
personalize = _resolve("merge", "personalize", interfaces.personalize)
ledger_feed = _resolve("ledger", "feed", _mock_ledger.feed)
cloud_status = _resolve("cloud", "status", interfaces.status)    # contract since D-020; sends nothing (I2)
LEDGER_IS_MOCK = MODES["ledger.feed"] == "mock"

EXTRAS: dict[str, bool] = {}


def _optional(module: str, attr: str) -> Optional[Callable]:
    """Non-contract helpers B offered (ledger.outbound, kb.stats, generalize.generalize). Used when
    present; the UI degrades quietly when they're missing. A broken module still raises on import."""
    fn = None
    if importlib.util.find_spec(f"core.{module}") is not None:
        fn = getattr(importlib.import_module(f"core.{module}"), attr, None)
    EXTRAS[f"{module}.{attr}"] = fn is not None
    return fn


ledger_outbound = _optional("ledger", "outbound")
kb_stats = _optional("kb", "stats")
generalize_flag = _optional("generalize", "generalize")
expected_notes_all = _optional("rules", "expected_notes_all")   # A, D-021: informational, never a Flag
expected_notes = _optional("rules", "expected_notes")
cloud_set_offline = _optional("cloud", "set_offline")            # B: "Wi-Fi off" for S6, no network
start_cover = _optional("router", "start_cover")                 # B: P6.6 cover traffic (G3)
stop_cover = _optional("router", "stop_cover")
cover_running = _optional("router", "cover_running")
COVER = os.environ.get("GV_COVER", "1") != "0"                   # GV_COVER=0 turns it off for local dev


def _note(kind: str, bytes_out: int = 0, bucket_id: Optional[str] = None) -> None:
    """Record an event in the mock ledger. Once B's ledger is real, B writes every entry itself."""
    if LEDGER_IS_MOCK:
        _mock_ledger.record(kind, bytes_out, bucket_id)


# --- helpers -----------------------------------------------------------------------------------

def _flags_for(drugs: list[Drug], profile: Profile) -> list[Flag]:
    """One flag per exact key. A finding can span several keys under one id (X5 is four flags:
    aspirin|ibuprofen, clopidogrel|ibuprofen, ibuprofen|lisinopril, ibuprofen|egfr<60), so dedupe by
    key, never by id. The same pair reached from both drugs (X2) still appears once."""
    seen: dict[str, Flag] = {}
    for drug in drugs:
        for flag in check(drug, profile):
            seen.setdefault(flag.key, flag)
    return sorted(seen.values(), key=lambda f: (f.id, f.key))


def _notes(raw: list[dict]) -> list[dict]:
    """Expected-combination notes from A (D-021): one per key, text passed through the I7 guard."""
    out: dict[str, dict] = {}
    for n in raw:
        text = merge.guard(n.get("text", ""))
        if text and n.get("key") not in out:
            out[n.get("key")] = {"id": n.get("id"), "key": n.get("key"), "text": text, "source": n.get("source", "")}
    return list(out.values())


def _cloud() -> dict:
    """{online, demo, forced_offline, toggle}: what the header badge shows. Never touches the network."""
    s = dict(cloud_status())
    return {"online": bool(s.get("online")), "demo": bool(s.get("demo", DEMO)),
            "forced_offline": bool(s.get("forced_offline", False)), "toggle": cloud_set_offline is not None}


def tier_label(fact: Fact) -> str:
    """Trust-tier label shown next to every fact (I6)."""
    if fact.tier == "cloud":
        return "AI-summarized, verify"
    return f"Curated: {fact.source}"


# --- API ---------------------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Cover traffic (P6.6) runs for as long as the app runs, so an observer can't tell when the user
    is actually asking. B's thread owns the schedule (GV_COVER_INTERVAL_S) and sends nothing while
    offline. Only stop what this app started."""
    started = bool(COVER and start_cover and start_cover())
    try:
        yield
    finally:
        if started and stop_cover:
            stop_cover()


def _cover_on() -> bool:
    return bool(cover_running and cover_running())


app = FastAPI(title="GenomeVault", docs_url=None, redoc_url=None, lifespan=lifespan)


_asked: deque[str] = deque(maxlen=10)   # recent questions, in memory only, for the visit summary


class OfflineIn(BaseModel):
    offline: bool


class CheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    via: Optional[str] = Field(default=None, pattern="^phone$")   # typed on the phone: also shown on the laptop


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return {"demo": DEMO, "disclaimer": DISCLAIMER, "modules": MODES, "extras": EXTRAS, "cloud": _cloud(),
            "cover": _cover_on()}


@app.get("/api/profile", response_model=Profile)
def profile() -> Profile:
    return load_profile()


@app.get("/api/flags")
def flags() -> dict:
    """Flags for the current medication list, all computed on device. Not a ledger event: the page
    loads this on every visit, and nothing leaves (keeps the ledger to things the user did)."""
    p = load_profile()
    result = _flags_for(p.meds, p)
    return {"checked": [d.ingredient for d in p.meds], "flags": [f.model_dump() for f in result],
            "notes": _notes(expected_notes_all(p) if expected_notes_all else [])}


def _check(drugs: list[Drug]) -> dict:
    """Flags and notes for some drugs against the profile, all on device (F3)."""
    p = load_profile()
    notes = [n for d in drugs for n in (expected_notes(d, p) if expected_notes else [])]
    return {"drugs": [d.model_dump() for d in drugs], "flags": [f.model_dump() for f in _flags_for(drugs, p)],
            "notes": _notes(notes)}


@app.post("/api/check")
def check_drug(body: CheckIn) -> dict:
    """Check one typed drug name against the profile (F2 typed input, F3)."""
    result = _check(to_ingredients(body.text))
    _note("local_only")
    if body.via == "phone" and result["drugs"]:
        _record_capture("typed", result)
    return {"input": body.text, **result}


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


@app.post("/api/offline")
def set_offline(body: OfflineIn) -> dict:
    """S6 "Wi-Fi off": B's forced-offline switch. Off means back to normal (GV_OFFLINE / network).
    Only the cloud is cut; local checks, stored answers and actions keep working (F8)."""
    if cloud_set_offline is None:
        raise HTTPException(409, "offline switch arrives with B's cloud module")
    cloud_set_offline(True if body.offline else None)
    return _cloud()


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
        "learned": kb_stats() if kb_stats else None,   # facts the KB holds (F6, E2)
        "cloud": _cloud(),                               # badge state, polled with the ledger
        "cover": _cover_on(),                            # cover traffic running (P6.6)
        "mock": LEDGER_IS_MOCK,
    }


@app.get("/api/ledger/{seq}/outbound")
def ledger_outbound_texts(seq: int) -> dict:
    """The exact texts that left in one ledger entry (S4). Shown on this device only; `mine` marks
    which of them came from this user's own flags, something only the device can know."""
    texts = ledger_outbound(seq) if ledger_outbound else []
    mine: list[int] = []
    if texts and generalize_flag:
        p = load_profile()
        real = set()
        for f in _flags_for(p.meds, p):
            try:
                real |= {t.text for t in generalize_flag(f)}
            except ValueError:
                continue   # a key generalize can't phrase is simply not marked
        mine = [i for i, t in enumerate(texts) if t in real]
    return {"seq": seq, "texts": texts, "mine": mine, "available": ledger_outbound is not None}


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
    s = actions.visit_summary(flags_now, p, list(_asked),
                              notes=_notes(expected_notes_all(p) if expected_notes_all else []))
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
:root { --paper:#fff; --ink:#02070A; --blue:#0297DE; --melon:#FFFFFF; --mute:#6b6b67; --line:#c3c3be; }
* { box-sizing: border-box; }
body { margin: 0; background: #02070A; color: var(--ink); font: 13px/1.45 "Helvetica Neue", Helvetica, Arial, sans-serif; }
.page { max-width: 780px; margin: 24px auto; padding: 40px 48px; background: var(--paper); }
.top { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 8px solid var(--blue); padding-bottom: 10px; }
h1 { margin: 0; font-size: 34px; font-weight: 500; letter-spacing: -.04em; }
.meta { color: var(--mute); font-size: 12px; text-align: right; }
section { display: grid; grid-template-columns: 170px 1fr; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
h2 { margin: 0; font-size: 12px; font-weight: 400; color: var(--mute); }
ul { margin: 0; padding: 0; list-style: none; }
li { padding: 2px 0; }
.note { margin-top: 16px; color: var(--mute); font-size: 11.5px; }
.bar { max-width: 780px; margin: 16px auto 0; display: flex; justify-content: space-between; font-size: 12px; }
.bar a:hover, .bar button:hover { border-color: var(--melon); color: var(--melon); }
.bar a, .bar button { color: #f2ede4; background: none; border: 1px solid #8d9ca6; padding: 6px 12px; font: inherit; cursor: pointer; text-decoration: none; }
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


# --- phone (F2, S2, S6): label photo in, reminders out; nothing leaves the local network --------

# The phone reaches the laptop over the local network, and this app holds the whole profile. So any
# request that isn't from this machine needs the pairing code shown on the laptop (Actions tab).
PHONE_CODE = (os.environ.get("GV_PHONE_CODE") or secrets.token_hex(3)).upper()
PHONE_URL = os.environ.get("GV_PHONE_URL", "")          # set by phone/serve_https.sh
PAIR_COOKIE = "gv_pair"
_LOCAL = {"127.0.0.1", "::1", "localhost", "testclient"}
_OPEN_PATHS = ("/phone", "/phone-assets/", "/api/phone/pair")
_fails = {"n": 0, "until": 0.0}
MAX_UPLOAD = 15 * 1024 * 1024
_captures: deque[dict] = deque(maxlen=20)
_capture_seq = {"n": 0}


def _is_local(request: Request) -> bool:
    return (request.client.host if request.client else "") in _LOCAL


def _paired(request: Request) -> bool:
    given = request.cookies.get(PAIR_COOKIE) or request.query_params.get("pair") or ""
    return secrets.compare_digest(given.upper(), PHONE_CODE)


@app.middleware("http")
async def phone_gate(request: Request, call_next):
    path = request.url.path
    if _is_local(request) or _paired(request) or path == "/phone" or path.startswith(_OPEN_PATHS[1:]):
        return await call_next(request)
    return JSONResponse({"detail": "pair this phone first: open /phone and enter the code on the laptop"},
                        status_code=401)


class PairIn(BaseModel):
    code: str = Field(min_length=4, max_length=16)


@app.post("/api/phone/pair")
def phone_pair(body: PairIn, request: Request) -> Response:
    """Phone enters the code shown on the laptop; a cookie then pairs it. Locks out after 10 misses."""
    now = time.time()
    if now < _fails["until"]:
        raise HTTPException(423, "too many wrong codes; try again in a few minutes")
    if not secrets.compare_digest(body.code.strip().upper(), PHONE_CODE):
        _fails["n"] += 1
        if _fails["n"] >= 10:
            _fails.update(n=0, until=now + 300)
        raise HTTPException(403, "wrong code")
    _fails["n"] = 0
    r = JSONResponse({"paired": True})
    r.set_cookie(PAIR_COOKIE, PHONE_CODE, httponly=True, samesite="strict",
                 secure=request.url.scheme == "https", max_age=12 * 3600)
    return r


@app.get("/api/phone")
def phone_info(request: Request) -> dict:
    """For the laptop only: the pairing code and the address to open on the phone."""
    if not _is_local(request):
        raise HTTPException(403, "shown on the laptop only")
    return {"code": PHONE_CODE, "url": PHONE_URL, "https": PHONE_URL.startswith("https://")}


def _record_capture(source: str, result: dict) -> None:
    _capture_seq["n"] += 1
    _captures.append({"seq": _capture_seq["n"], "ts": datetime.now(timezone.utc).isoformat(), "source": source,
                      "drugs": result["drugs"], "flags": [{"id": f["id"], "key": f["key"], "severity": f["severity"]}
                                                          for f in result["flags"]]})


@app.post("/api/capture")
async def capture(request: Request) -> dict:
    """Label photo from the phone (S2): raw image bytes in the body, its MIME type in Content-Type.
    A's capture.from_image reads it on this laptop; the photo itself is never stored or sent."""
    mime = request.headers.get("content-type", "")
    data = await request.body()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "photo too large")
    drugs = from_image(data, mime) if mime.startswith("image/") and data else []
    result = _check(drugs)
    _note("local_only")
    if drugs:
        _record_capture(request.headers.get("x-gv-source", "photo")[:12], result)
    return {"read": bool(drugs), **result}


@app.get("/api/captures")
def captures(since: int = 0) -> dict:
    """Recent phone captures, for the laptop's Medications tab."""
    return {"captures": [c for c in _captures if c["seq"] > since]}


@app.get("/phone", include_in_schema=False)
def phone_page() -> FileResponse:
    return FileResponse(PHONE_DIR / "index.html")


app.mount("/phone-assets", StaticFiles(directory=PHONE_DIR), name="phone")
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
