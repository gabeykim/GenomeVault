"""GenomeVault app (Agent C, M10): FastAPI backend for the two-pane UI.

Runs on localhost and makes no network calls itself (I2). Any cloud traffic happens inside
core/cloud.py, behind router.route.

Since G2 (D-032) every contract function comes from the real module on main: A's graph, rules,
normalize and capture, B's router, ledger and cloud, C's merge. The stand-ins are gone (D-014).
Non-contract helpers stay optional, so the UI degrades quietly if one is missing.
"""
from __future__ import annotations

import html
import importlib
import importlib.util
from contextlib import asynccontextmanager
import os
import re
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from core import actions, direct, intent, merge
from core.capture import from_image          # A, D-020: label photo -> drugs
from core.cloud import status as cloud_status  # contract since D-020; sends nothing (I2)
from core.contracts import Answer, Drug, Fact, Flag, Profile
from core.graph import load_profile
from core.ledger import feed as ledger_feed  # B writes every entry; the app never does
from core.merge import personalize
from core.normalize import to_ingredients
from core.router import route
from core.rules import check

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
PHONE_DIR = ROOT / "phone"
DEMO = os.environ.get("DEMO", "0") == "1"
DISCLAIMER = "Demo, not medical advice. All patient data is synthetic."


# --- contract functions: imported above as module-level names, so tests can monkeypatch them ----
# All real since G2 (D-032). /api/status keeps its "modules" shape for the team's ?debug view.
MODES: dict[str, str] = {name: "real" for name in (
    "graph.load_profile", "rules.check", "normalize.to_ingredients", "capture.from_image",
    "router.route", "merge.personalize", "ledger.feed", "cloud.status")}   # /api/status shape
LEDGER_IS_MOCK = False   # kept for B's tests/B/test_app_path*.py, which check it; always False now

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
no_data_keys = _optional("rules", "no_data_keys")                # A queue 8: pairs with no local entry (I4)
cloud_set_offline = _optional("cloud", "set_offline")            # B: "Wi-Fi off" for S6, no network
start_cover = _optional("router", "start_cover")                 # B: P6.6 cover traffic (G3)
stop_cover = _optional("router", "stop_cover")
cover_running = _optional("router", "cover_running")
sync_pack = _optional("router", "sync_pack")                     # B, D-027: whole knowledge pack, same for everyone
# D-040 adaptive questions, each behind its owner's flag; with them off (or missing) nothing changes.
suggest_names = _optional("normalize", "suggest")                # A part 1 (GV_FUZZY): typo -> assumed / choices
single_candidates = _optional("router", "single_candidates")     # B part 2: keys in neither partition
send_single = _optional("router", "send_single")                 # B part 4: one topic, only after consent
COVER = os.environ.get("GV_COVER", "1") != "0"                   # GV_COVER=0 turns it off for local dev


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
    if os.environ.get("GV_OCR", "").strip().lower() == "vlm":
        threading.Thread(target=_warm_vision_model, name="gv-vlm-warm", daemon=True).start()
    try:
        yield
    finally:
        if started and stop_cover:
            stop_cover()


VISION = {"configured": False, "warm": False, "seconds": None}


def _vision_configured() -> bool:
    """A's test for a usable vision model (A-025): LOCAL_VLM_MODEL set to a real model name."""
    try:
        from core import local_llm
    except ImportError:
        return False
    return (getattr(local_llm, "VLM_MODEL", "") or "") not in ("", "set-me")


def _warm_vision_model() -> None:
    """With GV_OCR=vlm the first label read loads the local vision model (~10 s). Read one synthetic
    sample label at startup so the S2 photo on stage takes ~4 s instead. Local only (I2).
    Without a configured model there is nothing to warm: say so instead of reporting "warm"."""
    VISION["configured"] = _vision_configured()
    if not VISION["configured"]:
        print("GenomeVault: GV_OCR=vlm but LOCAL_VLM_MODEL is not set; label photos won't be read "
              "(set it, e.g. qwen2.5vl:7b, or use GV_OCR=auto)", flush=True)
        return
    t0 = time.perf_counter()
    try:
        drugs = from_image((PHONE_DIR / "samples" / "aspirin.png").read_bytes(), "image/png")
        VISION.update(warm=bool(drugs), seconds=round(time.perf_counter() - t0, 1))
        print(f"GenomeVault: vision model {'warm' if drugs else 'did not read the warm-up label'} "
              f"({VISION['seconds']} s)", flush=True)
    except Exception as e:  # noqa: BLE001 - a cold model is slower, not broken
        print(f"GenomeVault: vision model warm-up failed ({type(e).__name__}); first read will be slow", flush=True)


def _cover_on() -> bool:
    return bool(cover_running and cover_running())


app = FastAPI(title="GenomeVault", docs_url=None, redoc_url=None, lifespan=lifespan)


_asked: deque[str] = deque(maxlen=10)   # recent questions, in memory only, for the visit summary


class OfflineIn(BaseModel):
    offline: bool


class CheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    via: Optional[str] = Field(default=None, pattern="^phone$")   # typed on the phone: also shown on the laptop
    no_assume: bool = False          # D-040 "Not what I meant"


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    no_assume: bool = False          # D-040 "Not what I meant": use the text exactly as typed


class SingleIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    key: str = Field(min_length=3, max_length=120)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return {"demo": DEMO, "disclaimer": DISCLAIMER, "modules": MODES, "extras": EXTRAS, "cloud": _cloud(),
            "cover": _cover_on(),
            "adaptive": {"fuzzy": _fuzzy_on(), "single": _single_on()},
            "vision": {"mode": os.environ.get("GV_OCR", "auto").strip().lower(), **VISION}}


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
    no_data = sorted({k for d in drugs for k in (no_data_keys(d, p) if no_data_keys else [])})
    return {"drugs": [d.model_dump() for d in drugs], "flags": [f.model_dump() for f in _flags_for(drugs, p)],
            "notes": _notes(notes), "no_data": no_data}


# ---------- D-040 adaptive questions (C part 4) ----------

def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _fuzzy_on() -> bool:
    return bool(suggest_names) and _flag("GV_FUZZY")


def _single_on() -> bool:
    return bool(single_candidates and send_single)


def _suggestions(text: str) -> list[dict]:
    """A's normalize.suggest, read defensively: [{term, assumed, choices}] for each unmatched drug-like
    token. Never used to look anything up until it is on screen (I4): assumed names are shown with the
    answer, choices hold the answer until the user picks."""
    if not _fuzzy_on():
        return []
    try:
        raw = suggest_names(text) or []
    except Exception:  # noqa: BLE001 - a suggestion failure must not break the check
        return []
    out = []
    for item in raw:
        get = item.get if isinstance(item, dict) else (lambda k, i=item: getattr(i, k, None))
        term = get("term") or get("token")
        if not term:
            continue
        choices = [str(c) for c in (get("choices") or get("options") or []) if c][:3]
        assumed = get("assumed")
        span = get("span")
        span = (int(span[0]), int(span[1])) if isinstance(span, (list, tuple)) and len(span) == 2 else None
        out.append({"term": str(term)[:60], "assumed": str(assumed) if assumed else None, "choices": choices,
                    "span": span, "not_covered": [str(c) for c in (get("not_covered") or [])]})
    return out


def _swap(text: str, term: str, name: str) -> str:
    """Replace the first whole-word `term`. A hyphen is a word boundary, so the typo in a combo like
    "lisinoprl-hydrochlorothiazide" is swapped too (A, to-C 1720)."""
    return re.sub(rf"(?<!\w){re.escape(term)}(?!\w)", lambda _m: name, text, count=1, flags=re.IGNORECASE)


def _apply_swaps(text: str, swaps: list[tuple[Optional[tuple[int, int]], str, str]]) -> str:
    """Apply (span, term, name) swaps. Spans from A's suggest index the typed text; apply them right to
    left so earlier spans stay valid. A span that doesn't hold `term` falls back to a word match."""
    by_span = [(sp, t, n) for sp, t, n in swaps if sp and text[sp[0]:sp[1]].lower() == t.lower()]
    rest = [(sp, t, n) for sp, t, n in swaps if (sp, t, n) not in by_span]
    for (a, b), _t, name in sorted(by_span, key=lambda x: x[0][0], reverse=True):
        text = text[:a] + name + text[b:]
    for _sp, term, name in rest:
        text = _swap(text, term, name)
    return text


def _adapt(text: str, no_assume: bool) -> tuple[str, list[dict], list[dict]]:
    """(text to use, assumed [{term, name}], held [{term, choices}]) for one typed check or question."""
    assumed, held, swaps = [], [], []
    for sug in _suggestions(text):
        if sug["assumed"] and not no_assume:
            swaps.append((sug["span"], sug["term"], sug["assumed"]))
            assumed.append({"term": sug["term"], "name": sug["assumed"]})
        elif sug["choices"] and not sug["assumed"]:
            held.append({"term": sug["term"], "choices": sug["choices"], "not_covered": sug["not_covered"]})
    return _apply_swaps(text, swaps), assumed, held


@app.post("/api/check")
def check_drug(body: CheckIn) -> dict:
    """Check one typed drug name against the profile (F2 typed input, F3)."""
    text, assumed, held = _adapt(body.text, body.no_assume)
    if held:   # "Did you mean ...?": nothing is checked until the user picks (D-040)
        return {"input": body.text, "drugs": [], "flags": [], "notes": [], "no_data": [],
                "held": True, "choices": held}
    result = _check(to_ingredients(text))
    if body.via == "phone" and result["drugs"]:
        _record_capture("typed", result)
    out = {"input": body.text, **result}
    if assumed:
        out["assumed"] = assumed
    return out


def _named_drugs(question: str, p: Profile) -> list[Drug]:
    """Drugs the question names that aren't already on the med list (B-025): their local flags go to the
    router too, so "Can I take ibuprofen?" is covered by X5 like a typed ibuprofen check."""
    on_list = {m.ingredient for m in p.meds}
    return [d for d in to_ingredients(question) if d.ingredient not in on_list]


def _answer_payload(answer: Answer, current: list[Flag], p: Profile) -> dict:
    return {
        "state": answer.state,
        "text": personalize(answer, current, p),
        # Same content as "text", as ordered sections, so the UI can lead with the asked pair (C-021).
        "sections": merge.structure(answer, current, p),
        "facts": [{**f.model_dump(mode="json"), "label": tier_label(f)} for f in answer.facts],
        "sent_to_cloud": answer.sent_to_cloud,
    }


def _single_keys(question: str, current: list[Flag]) -> list[str]:
    """Keys the question needs that no fixed group covers (B, D-040). Only offered while online."""
    if not _single_on() or not _cloud()["online"]:
        return []
    try:
        return [str(k) for k in (single_candidates(question, current) or [])][:3]
    except Exception:  # noqa: BLE001 - no offer is the safe default
        return []


@app.post("/api/ask")
def ask(body: AskIn) -> dict:
    """Open question: router decides what (if anything) leaves; merge personalizes locally."""
    question, assumed, held = _adapt(body.question, body.no_assume)
    if held:   # "Did you mean ...?": nothing is routed or sent until the user picks (D-040, I4)
        return {"state": "held", "text": "", "sections": [], "facts": [], "sent_to_cloud": False,
                "choices": held}
    p = load_profile()
    extra: dict = {}
    if intent.enabled():  # GV_INTENT=1 (D-040): on-device canonical rewrite, then the normal route()
        u = intent.canonicalize(question, _flags_for(p.meds + _named_drugs(question, p), p))
        question = u.question
        extra = {"understood_as": u.understood_as, "clarify": u.clarify}
    current = _flags_for(p.meds + _named_drugs(question, p), p)
    answer: Answer = route(question, current)
    _asked.append(question)
    out = {**_answer_payload(answer, current, p), **extra}
    if direct.enabled():  # GV_DIRECT=1: answer-first lead line, composed on device from flags/facts only
        line = direct.direct_line(question, answer, current, p, original=body.question)
        if line:
            out["sections"], out["text"] = direct.apply(out["sections"], out["text"], line)
    if assumed:
        out["assumed"] = assumed
    if answer.state == "no_data":
        keys = _single_keys(question, current)
        if keys:   # can't be hidden in a group of 8: ask first, send nothing yet
            out["consent"] = {"question": question, "keys": keys}
    return out


@app.post("/api/ask/single")
def ask_single(body: SingleIn) -> dict:
    """The user said yes to sending one question on its own, not hidden in a group (D-040). The key is
    re-derived here, so the page can only consent to what the router itself offered."""
    if not _single_on():
        raise HTTPException(409, "single send arrives with B's router (D-040)")
    if not _cloud()["online"]:
        raise HTTPException(409, "offline: nothing can be sent")
    p = load_profile()
    current = _flags_for(p.meds + _named_drugs(body.question, p), p)
    if body.key not in _single_keys(body.question, current):
        raise HTTPException(400, "that question doesn't need a single send")
    answer: Answer = send_single(body.key)
    _asked.append(body.question)
    return {**_answer_payload(answer, current, p), "single": True}


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
        "entries": [{**e.model_dump(mode="json"), "pack": e.seq in _pack_seqs} for e in everything if e.seq > since],
        "totals": {
            "count": len(everything),
            "bytes_out": sum(e.bytes_out for e in everything),
            "personal_fields_sent": sum(e.personal_fields_sent for e in everything),
        },
        "learned": kb_stats() if kb_stats else None,   # facts the KB holds (F6, E2)
        "cloud": _cloud(),                               # badge state, polled with the ledger
        "cover": _cover_on(),                            # cover traffic running (P6.6)
    }


@app.get("/api/ledger/{seq}/outbound")
def ledger_outbound_texts(seq: int) -> dict:
    """The exact texts that left in one ledger entry (S4). Shown on this device only; `mine` marks
    which of them came from this user's own flags, something only the device can know."""
    texts = ledger_outbound(seq) if ledger_outbound else []
    mine: list[int] = []
    entry = next((e for e in ledger_feed(seq - 1) if e.seq == seq), None)
    # Only a real question group can hold "yours". Cover traffic and the knowledge pack are drawn the
    # same for everyone, so a matching topic there is coincidence, not something the user asked.
    if texts and generalize_flag and entry is not None and entry.kind == "bucket" and seq not in _pack_seqs:
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
.bar a:hover, .bar button:hover { background: var(--ink); color: var(--paper); }
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


# --- knowledge pack (D-027): the whole fixed partition, the same for every user -------------------

_sync: dict = {"running": False, "result": None, "finished": None}
_pack_seqs: set[int] = set()
_sync_lock = threading.Lock()


def _last_seq() -> int:
    entries = ledger_feed(0)
    return entries[-1].seq if entries else 0


def _run_sync() -> None:
    """Runs B's sync_pack() off the request thread (instant in demo mode, ~3 minutes live). Cover traffic
    pauses meanwhile, so every row sent in this window is the pack and can be labeled as such."""
    paused = bool(_cover_on() and stop_cover)
    if paused:
        stop_cover()
    before = _last_seq()
    try:
        result = sync_pack()
    except Exception as e:                       # never leave the button stuck on "Syncing"
        result = {"error": type(e).__name__}
    finally:
        _pack_seqs.update(e.seq for e in ledger_feed(before) if e.kind in ("cover", "bucket", "blocked"))
        if paused and start_cover:
            start_cover()
    _sync.update(running=False, result=result, finished=datetime.now(timezone.utc).isoformat())


@app.post("/api/sync")
def start_sync() -> dict:
    """Start a knowledge-pack sync. Nothing about the user chooses what is sent (I5): every user downloads
    the same groups, in shuffled order, each through the leakage check."""
    if sync_pack is None:
        raise HTTPException(409, "knowledge pack arrives with B's router")
    if not _cloud()["online"]:
        raise HTTPException(409, "offline: connect to sync the knowledge pack")
    with _sync_lock:
        if _sync["running"]:
            raise HTTPException(409, "already syncing")
        _sync.update(running=True, result=None, finished=None)
    threading.Thread(target=_run_sync, name="gv-sync", daemon=True).start()
    return sync_status()


@app.get("/api/sync")
def sync_status() -> dict:
    return {"available": sync_pack is not None, **_sync}


# --- phone (F2, S2, S6): label photo in, reminders out; nothing leaves the local network --------

# The phone reaches the laptop over the local network, and this app holds the whole profile. So any
# request that isn't from this machine needs the pairing code shown on the laptop (Actions tab).
PHONE_CODE = (os.environ.get("GV_PHONE_CODE") or secrets.token_hex(3)).upper()
def _phone_url() -> str:
    """Where the phone opens /phone. phone/serve_https.sh sets GV_PHONE_URL on a laptop; in a GitHub
    Codespace (the README's "Open in Codespaces" link) the forwarded HTTPS address is known from the
    environment. Nothing is looked up over the network (I2)."""
    if os.environ.get("GV_PHONE_URL"):
        return os.environ["GV_PHONE_URL"]
    name, domain = os.environ.get("CODESPACE_NAME"), os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    if name and domain:
        return f"https://{name}-{os.environ.get('GV_PORT', '8000')}.{domain}/phone"
    return ""


PHONE_URL = _phone_url()
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


_UI_PATHS = ("/ui/", "/phone-assets/")


@app.middleware("http")
async def no_stale_ui(request: Request, call_next):
    """The page and its files are revalidated on every load (their ETag keeps that cheap), so a UI fix
    shows up on the next reload instead of hiding behind a browser's cached copy."""
    response = await call_next(request)
    path = request.url.path
    if path in ("/", "/phone", "/summary") or path.startswith(_UI_PATHS):
        response.headers["Cache-Control"] = "no-cache"
    return response


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
    # The on-device vision model takes ~4 s a label (GV_OCR=vlm): read off the event loop so the
    # laptop UI keeps polling meanwhile.
    drugs = await run_in_threadpool(from_image, data, mime) if mime.startswith("image/") and data else []
    # D-029: only report what was read. The user confirms or edits it on the phone before rules run.
    return {"read": bool(drugs), "drugs": [d.model_dump() for d in drugs]}


class ConfirmIn(BaseModel):
    drugs: list[Drug] = Field(min_length=1, max_length=5)
    source: Literal["photo", "sample"] = "photo"


@app.post("/api/capture/confirm")
def capture_confirm(body: ConfirmIn) -> dict:
    """The user confirmed the drug read from a label: run the local check and show it on the laptop."""
    drugs = [Drug(ingredient=d.ingredient.strip().lower()[:60], dose_mg=d.dose_mg) for d in body.drugs]
    result = _check(drugs)
    _record_capture(body.source, result)
    return result


@app.get("/api/captures")
def captures(since: int = 0) -> dict:
    """Recent phone captures, for the laptop's Medications tab."""
    return {"captures": [c for c in _captures if c["seq"] > since]}


@app.get("/phone", include_in_schema=False)
def phone_page() -> FileResponse:
    return FileResponse(PHONE_DIR / "index.html")


app.mount("/phone-assets", StaticFiles(directory=PHONE_DIR), name="phone")
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
