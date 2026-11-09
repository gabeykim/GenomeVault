"""Cloud client (F4, M8). The only module in the app that makes outbound network calls (I2).

What it accepts: generalized `Topic`s only (P6.3). It never sees a Profile, a Flag or the user's
question, so it cannot leak them. The router runs the leakage check (I3) *before* calling here and
writes the ledger entry (P6.8) after.

Sessions (P6.4): every call to `ask_bucket` opens a fresh HTTP client (new connection, no cookies,
no conversation history) and closes it afterwards, and every Topic is its own single-turn request.
Nothing links one bucket's requests to another's except timing, and timing is randomized: before
every request `pause()` sleeps a random delay drawn from `delay_range()` (P6.4, queue 8), so the
requests of two buckets needed by one question do not arrive as one tight burst.

Results are `Fact(tier="cloud")` with a short expiry (I6: "AI-summarized, verify", expires sooner).

Configuration (environment only, never in the repo, AGENTS.md §10):
- `GV_CLOUD_MODEL`   model id (default `claude-sonnet-5-5`)
- `ANTHROPIC_API_KEY` API key; required for live calls only
- `GV_CLOUD_URL`     Messages endpoint (default Anthropic's)
- `GV_CLOUD_TTL_DAYS` cloud fact lifetime in days (default 30)
- `DEMO=1`           replay `mocks/cloud_cache/` instead of the network (I8)
- `GV_CLOUD_CACHE`   alternative cache directory (tests, recording)
- `GV_OFFLINE=1`     force offline mode (F8, E4): nothing is sent, not even demo replay
- `GV_DELAY_S=lo,hi` random pause before each request, in seconds (default `0.3,2.0` live, `0,0` in
                     demo mode, where nothing leaves the device and a slow demo helps nobody)
- `GV_DEMO_LIVE_FALLBACK=1` (D-040 part 3, default off) with `DEMO=1`: a bucket with a key missing from
                     the replay cache is asked live, whole (I5), when a key is set. Forced offline still wins.

Offline mode (F8, queue 9): `offline()` is True when forced (`GV_OFFLINE=1` or `set_offline(True)`).
Forced offline wins over `DEMO=1`, so the offline demo beat (S6, ibuprofen X5) runs with demo mode on
and Wi-Fi "off". `status()` reports what this module already knows and never sends anything:
`online` is False when forced offline, when live mode has no API key, or when the last live call
failed (it turns True again after the next successful call).

Cache format (demo replay): any number of `*.json` files in the cache dir, each a JSON object
`{"<exact key>": "<answer text>", ...}`. A key missing from the cache gets no Fact, which the
router turns into `no_data` (I4: never invent an answer). Record a cache with
`ANTHROPIC_API_KEY=... python -m core.cloud record <out_dir>`, which writes one `<bucket_id>.json`
per bucket of the current partition and skips buckets already fully recorded (restartable).
Vet it with `python -m core.cloud check [<cache_dir>]` (exit 0 = every partition key has an answer
that passes the I7 wording check).

Demo live fallback (D-040 part 3): with `DEMO=1` and `GV_DEMO_LIVE_FALLBACK=1`, if any requested key
has no cached answer and `ANTHROPIC_API_KEY` is set, *every* requested topic of the bucket is asked live
(the whole bucket, never just the missing key, so the request pattern does not single it out, I5),
with the live delays (P6.4). Cached answers (the reviewed pack, D-027) are kept for keys that have
one; live answers fill the rest and carry the live source. If the live call fails, the replayed
answers are returned alone (missing keys read as `no_data`, I4) and `status()` stays demo-online.
Without the flag, demo mode never touches the network (I8).

I7 filter: every answer, live or replayed, goes through `validator.check_wording`. One that says
"safe" or tells the reader to start/stop/change a medicine is dropped, so its key reads as `no_data`.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import random
import sys
import time
from datetime import date, timedelta
from typing import Iterable, Optional

import httpx

from .contracts import Bucket, Fact, Topic
from .validator import check_wording, wording_problems

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "mocks" / "cloud_cache"
DEFAULT_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"
API_VERSION = "2023-06-01"
MAX_TOKENS = 1000                    # D-026: 400 cut ~25% of answers off inside a thinking block
# D-026: the model thinks by default; the API rejects {"type": "disabled"} for it (HTTP 400) and names
# "between_tools" as the off switch for a request with no tools.
THINKING = {"type": "between_tools"}
TIMEOUT_S = 30.0
log = logging.getLogger(__name__)
_transport: Optional[httpx.BaseTransport] = None   # tests inject httpx.MockTransport; None = real network
LIVE_DELAY_S = (0.3, 2.0)
_sleep = time.sleep                  # tests inject a recorder
_rng = random.SystemRandom()         # OS entropy: delays are not reproducible from a seed

SYSTEM_PROMPT = (
    "You are a clinical pharmacology reference. Answer the general question in 2 to 4 plain sentences "
    "for a patient preparing to talk to a pharmacist. Describe what is known about the interaction or "
    "effect across the whole population or range asked about. Do not address the reader's personal "
    "situation, do not say anything is safe, and do not tell anyone to start, stop or change a "
    "medicine. If nothing is established, say so. "
    # D-027 note: the knowledge pack was recorded with this sentence; it stops answers that only
    # describe a guideline from tripping the I7 filter ("the standard dose is recommended").
    "Write in neutral reporting style about what sources state, for example 'the CPIC guideline lists "
    "an alternative agent for poor metabolizers'. Never write is recommended, are advised, is "
    "preferred, should, or any sentence telling people or patients what to do."
)


class CloudUnavailable(RuntimeError):
    """Forced offline, no network, no API key, or the provider failed. The router falls back to
    P6 steps 1-2 only (F8)."""


_forced: Optional[bool] = None        # set_offline() override; None = follow GV_OFFLINE
_last_failure: Optional[str] = None   # reason the last live call failed; None after a success


def _truthy(v: str) -> bool:
    return v not in ("", "0", "false", "False")


def set_offline(value: Optional[bool]) -> None:
    """Force offline on/off at runtime (UI toggle, eval cold/warm runs). None = follow GV_OFFLINE."""
    global _forced
    _forced = value


def offline() -> bool:
    """True when offline mode is forced. The router then sends nothing (P6 steps 1-2 only)."""
    if _forced is not None:
        return _forced
    return _truthy(os.environ.get("GV_OFFLINE", ""))


def status() -> dict:
    """`{"online": bool, "demo": bool, "forced_offline": bool}`. Never touches the network."""
    forced = offline()
    demo = demo_mode()
    if forced:
        online = False
    elif demo:
        online = True                                   # replay always answers (I8)
    else:
        online = bool(os.environ.get("ANTHROPIC_API_KEY")) and _last_failure is None
    return {"online": online, "demo": demo, "forced_offline": forced}


def demo_mode() -> bool:
    return _truthy(os.environ.get("DEMO", ""))


def demo_live_fallback() -> bool:
    """D-040 part 3: True when `DEMO=1` may fall back to a live call on a cache miss (flag set)."""
    return demo_mode() and _truthy(os.environ.get("GV_DEMO_LIVE_FALLBACK", ""))


def model() -> str:
    return os.environ.get("GV_CLOUD_MODEL", DEFAULT_MODEL)


def ttl_days() -> int:
    return int(os.environ.get("GV_CLOUD_TTL_DAYS", "30"))


def delay_range(live: Optional[bool] = None) -> tuple[float, float]:
    """(lo, hi) seconds of random pause before each request (P6.4). Bad values are an error.
    `live` None = follow the mode (demo replay 0,0); True = a real request (demo live fallback)."""
    raw = os.environ.get("GV_DELAY_S")
    if raw is None:
        live = (not demo_mode()) if live is None else live
        return LIVE_DELAY_S if live else (0.0, 0.0)
    lo, hi = (float(x) for x in raw.split(","))
    if lo < 0 or hi < lo:
        raise ValueError(f"GV_DELAY_S must be 'lo,hi' with 0 <= lo <= hi, got {raw!r}")
    return lo, hi


def pause(live: Optional[bool] = None) -> float:
    """Sleep a random delay from `delay_range(live)`; returns the seconds slept (0 when disabled)."""
    lo, hi = delay_range(live)
    if hi <= 0:
        return 0.0
    d = _rng.uniform(lo, hi)
    _sleep(d)
    return d


def cache_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("GV_CLOUD_CACHE", str(DEFAULT_CACHE)))


def load_cache(path: Optional[pathlib.Path] = None) -> dict[str, str]:
    """All cached key → text pairs. Malformed files are an error, not silently skipped."""
    path = path or cache_dir()
    out: dict[str, str] = {}
    if not path.is_dir():
        return out
    for f in sorted(path.glob("*.json")):
        data = json.loads(f.read_text())
        if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
            raise ValueError(f"{f}: cloud cache must be a JSON object of key -> text")
        out.update(data)
    return out


def _fact(key: str, text: str, source: str, today: Optional[date] = None) -> Fact:
    today = today or date.today()
    return Fact(key=key, text=text.strip(), tier="cloud", source=source,
                fetched=today, expires=today + timedelta(days=ttl_days()))


def _ask_live(client: httpx.Client, topic: Topic, api_key: str) -> str:
    r = client.post(
        os.environ.get("GV_CLOUD_URL", DEFAULT_URL),
        headers={"x-api-key": api_key, "anthropic-version": API_VERSION, "content-type": "application/json"},
        json={"model": model(), "max_tokens": MAX_TOKENS, "thinking": THINKING, "system": SYSTEM_PROMPT,
              "messages": [{"role": "user", "content": topic.text}]},
    )
    r.raise_for_status()
    body = r.json()
    text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")
    if not text.strip():
        # D-026: still no_data (I4), but say so instead of dropping it silently. Logs the bucket key
        # only (a generalized concept), never anything about the user.
        log.warning("cloud: empty answer for %s (stop_reason=%s); reads as no_data",
                    topic.key, body.get("stop_reason"))
    return text


def ask_bucket(bucket: Bucket, topics: Iterable[Topic]) -> list[Fact]:
    """Ask every Topic of one bucket in its own session; return one cloud Fact per answered key.

    Every topic key must belong to `bucket` (I5: we only ever send whole fixed buckets).
    Raises CloudUnavailable if a live call cannot be made; demo mode never touches the network.
    """
    topics = list(topics)
    stray = [t.key for t in topics if t.key not in bucket.keys]
    if stray:
        raise ValueError(f"topics outside bucket {bucket.id}: {stray}")

    if offline():
        raise CloudUnavailable("offline mode")
    if demo_mode():
        answers = _demo_answers(bucket, topics)
    else:
        source, live = _answers(bucket, topics)
        answers = [(k, text, source) for k, text in live]
    # I7: an answer that says "safe" or gives a start/stop instruction is dropped -> no_data (I4)
    return [_fact(k, text, source) for k, text, source in answers if check_wording(text)]


def ask_single(topic: Topic) -> Optional[Fact]:
    """D-040 part 2, consented single send: ONE generalized topic on its own, NOT hidden in a bucket.
    Only the router's `send_single` calls this, after the user said yes and the leakage check passed.
    Demo mode replays the cache and goes live only with GV_DEMO_LIVE_FALLBACK and a key. Same I7 filter.
    Returns None when there is no usable answer; raises CloudUnavailable if nothing could be sent."""
    if offline():
        raise CloudUnavailable("offline mode")
    if demo_mode():
        cached = load_cache().get(topic.key, "").strip()
        if cached:
            pause()
            return _fact(topic.key, cached, "cloud-cache:single") if check_wording(cached) else None
        if not (demo_live_fallback() and os.environ.get("ANTHROPIC_API_KEY")):
            return None
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise CloudUnavailable("ANTHROPIC_API_KEY not set")
    global _last_failure
    try:
        with httpx.Client(timeout=TIMEOUT_S, transport=_transport) as client:
            pause(live=True)
            text = _ask_live(client, topic, api_key).strip()
    except httpx.HTTPError as e:
        _last_failure = type(e).__name__
        raise CloudUnavailable(f"cloud call failed: {type(e).__name__}") from e
    _last_failure = None
    if not text or not check_wording(text):
        return None
    return _fact(topic.key, text, f"cloud:{model()}")


def _demo_answers(bucket: Bucket, topics: list[Topic]) -> list[tuple[str, str, str]]:
    """[(key, raw text, source)] from replay, plus the live fallback when flagged (D-040 part 3)."""
    source, replayed = _answers(bucket, topics)
    out = [(k, text, source) for k, text in replayed]
    missing = len(out) < len(topics)
    if not (missing and demo_live_fallback() and os.environ.get("ANTHROPIC_API_KEY")):
        return out
    try:
        live_source, live = _answers(bucket, topics, live=True)   # the whole bucket, never one key (I5)
    except CloudUnavailable as e:
        log.warning("cloud: demo live fallback for bucket %s failed (%s); replay only", bucket.id, e)
        return out
    have = {k for k, _, _ in out}
    return out + [(k, text, live_source) for k, text in live if k not in have]


def _answers(bucket: Bucket, topics: list[Topic], live: bool = False) -> tuple[str, list[tuple[str, str]]]:
    """(source, [(key, raw non-blank text)]) from demo replay or the live API. No I7 filter.
    `live=True` forces the live API even in demo mode (demo live fallback)."""
    if offline():
        raise CloudUnavailable("offline mode")
    if demo_mode() and not live:
        cache = load_cache()
        out = []
        for t in topics:
            pause()
            if cache.get(t.key, "").strip():
                out.append((t.key, cache[t.key]))
        return f"cloud-cache:{bucket.version}", out

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise CloudUnavailable("ANTHROPIC_API_KEY not set")
    global _last_failure
    out: list[tuple[str, str]] = []
    try:
        with httpx.Client(timeout=TIMEOUT_S, transport=_transport) as client:   # one session per bucket
            for t in topics:
                pause(live=True)
                text = _ask_live(client, t, api_key)
                if text.strip():
                    out.append((t.key, text.strip()))
    except httpx.HTTPError as e:
        _last_failure = type(e).__name__
        raise CloudUnavailable(f"cloud call failed: {type(e).__name__}") from e
    _last_failure = None
    return f"cloud:{model()}", out


def record(out_dir: pathlib.Path, resume: bool = True) -> int:
    """Fetch every bucket live and write `<bucket_id>.json` caches for demo replay. Returns key count.

    Writes raw answers (including ones I7 will drop at replay) so `check` can show them; replay
    filters them anyway. With `resume`, a bucket whose file already holds all its keys is skipped,
    so a run that died halfway (rate limit, network) can be restarted without paying twice.
    """
    from .decoys import load_buckets
    from .generalize import topic_for_key

    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for b in load_buckets():
        f = out_dir / f"{b.id}.json"
        if resume and f.is_file():
            done = json.loads(f.read_text())
            if isinstance(done, dict) and all(str(done.get(k, "")).strip() for k in b.keys):
                n += len(b.keys)
                continue
        _, answers = _answers(b, [topic_for_key(k) for k in b.keys])
        f.write_text(json.dumps(dict(answers), indent=2) + "\n")
        n += len(answers)
    return n


def check_cache(path: Optional[pathlib.Path] = None) -> dict:
    """Vet a demo cache before rehearsal (I7, I8). Never touches the network.

    Returns `{"universe", "answered", "missing", "rejected", "unknown", "ok"}`: `missing` keys of the
    current partition with no answer (they replay as `no_data`), `rejected` key -> I7 problems
    (dropped at replay), `unknown` cached keys outside the partition. `ok` = nothing missing or rejected.
    """
    from .decoys import universe

    cache = load_cache(path)
    keys = universe()
    answered = [k for k in keys if cache.get(k, "").strip()]
    rejected = {k: p for k in answered if (p := wording_problems(cache[k]))}
    missing = [k for k in keys if k not in answered]
    unknown = sorted(set(cache) - set(keys))
    return {"universe": len(keys), "answered": len(answered) - len(rejected), "missing": missing,
            "rejected": rejected, "unknown": unknown, "ok": not missing and not rejected}


def _main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "record":
        print(f"recorded {record(pathlib.Path(argv[1]))} answers")
        return 0
    if argv[:1] == ["check"] and len(argv) <= 2:
        r = check_cache(pathlib.Path(argv[1]) if len(argv) == 2 else None)
        print(f"{r['answered']}/{r['universe']} keys usable; {len(r['missing'])} missing, "
              f"{len(r['rejected'])} rejected (I7), {len(r['unknown'])} outside the partition")
        for k in r["missing"]:
            print(f"  missing  {k}")
        for k, probs in r["rejected"].items():
            print(f"  rejected {k}: {'; '.join(probs)}")
        for k in r["unknown"]:
            print(f"  unknown  {k}")
        return 0 if r["ok"] else 1
    print("usage: python -m core.cloud record <out_dir> | check [<cache_dir>]")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
