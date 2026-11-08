"""Cloud client (F4, M8). The only module in the app that makes outbound network calls (I2).

What it accepts: generalized `Topic`s only (P6.3). It never sees a Profile, a Flag or the user's
question, so it cannot leak them. The router runs the leakage check (I3) *before* calling here and
writes the ledger entry (P6.8) after.

Sessions (P6.4): every call to `ask_bucket` opens a fresh HTTP client (new connection, no cookies,
no conversation history) and closes it afterwards, and every Topic is its own single-turn request.
Nothing links one bucket's requests to another's except timing; randomized delays are queue 8.

Results are `Fact(tier="cloud")` with a short expiry (I6: "AI-summarized, verify", expires sooner).

Configuration (environment only, never in the repo, AGENTS.md §10):
- `GV_CLOUD_MODEL`   model id (default `claude-sonnet-5-5`)
- `ANTHROPIC_API_KEY` API key; required for live calls only
- `GV_CLOUD_URL`     Messages endpoint (default Anthropic's)
- `GV_CLOUD_TTL_DAYS` cloud fact lifetime in days (default 30)
- `DEMO=1`           replay `mocks/cloud_cache/` instead of the network (I8)
- `GV_CLOUD_CACHE`   alternative cache directory (tests, recording)

Cache format (demo replay): any number of `*.json` files in the cache dir, each a JSON object
`{"<exact key>": "<answer text>", ...}`. A key missing from the cache gets no Fact, which the
router turns into `no_data` (I4: never invent an answer). Record a cache with
`ANTHROPIC_API_KEY=... python -m core.cloud record <out_dir>`, which writes one `<bucket_id>.json`
per bucket of the current partition.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import date, timedelta
from typing import Iterable, Optional

import httpx

from .contracts import Bucket, Fact, Topic

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "mocks" / "cloud_cache"
DEFAULT_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"
API_VERSION = "2023-06-01"
MAX_TOKENS = 400
TIMEOUT_S = 30.0
_transport: Optional[httpx.BaseTransport] = None   # tests inject httpx.MockTransport; None = real network

SYSTEM_PROMPT = (
    "You are a clinical pharmacology reference. Answer the general question in 2 to 4 plain sentences "
    "for a patient preparing to talk to a pharmacist. Describe what is known about the interaction or "
    "effect across the whole population or range asked about. Do not address the reader's personal "
    "situation, do not say anything is safe, and do not tell anyone to start, stop or change a "
    "medicine. If nothing is established, say so."
)


class CloudUnavailable(RuntimeError):
    """No network, no API key, or the provider failed. The router falls back (queue 9)."""


def demo_mode() -> bool:
    return os.environ.get("DEMO", "") not in ("", "0", "false", "False")


def model() -> str:
    return os.environ.get("GV_CLOUD_MODEL", DEFAULT_MODEL)


def ttl_days() -> int:
    return int(os.environ.get("GV_CLOUD_TTL_DAYS", "30"))


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
        json={"model": model(), "max_tokens": MAX_TOKENS, "system": SYSTEM_PROMPT,
              "messages": [{"role": "user", "content": topic.text}]},
    )
    r.raise_for_status()
    body = r.json()
    return "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")


def ask_bucket(bucket: Bucket, topics: Iterable[Topic]) -> list[Fact]:
    """Ask every Topic of one bucket in its own session; return one cloud Fact per answered key.

    Every topic key must belong to `bucket` (I5: we only ever send whole fixed buckets).
    Raises CloudUnavailable if a live call cannot be made; demo mode never touches the network.
    """
    topics = list(topics)
    stray = [t.key for t in topics if t.key not in bucket.keys]
    if stray:
        raise ValueError(f"topics outside bucket {bucket.id}: {stray}")

    if demo_mode():
        cache = load_cache()
        source = f"cloud-cache:{bucket.version}"
        return [_fact(t.key, cache[t.key], source) for t in topics if cache.get(t.key, "").strip()]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise CloudUnavailable("ANTHROPIC_API_KEY not set")
    facts: list[Fact] = []
    source = f"cloud:{model()}"
    try:
        with httpx.Client(timeout=TIMEOUT_S, transport=_transport) as client:   # one session per bucket
            for t in topics:
                text = _ask_live(client, t, api_key)
                if text.strip():
                    facts.append(_fact(t.key, text, source))
    except httpx.HTTPError as e:
        raise CloudUnavailable(f"cloud call failed: {type(e).__name__}") from e
    return facts


def record(out_dir: pathlib.Path) -> int:
    """Fetch every bucket live and write `<bucket_id>.json` caches for demo replay. Returns key count."""
    from .decoys import load_buckets
    from .generalize import topic_for_key

    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for b in load_buckets():
        facts = ask_bucket(b, [topic_for_key(k) for k in b.keys])
        (out_dir / f"{b.id}.json").write_text(json.dumps({f.key: f.text for f in facts}, indent=2) + "\n")
        n += len(facts)
    return n


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "record":
        print(f"recorded {record(pathlib.Path(sys.argv[2]))} answers")
    else:
        print("usage: python -m core.cloud record <out_dir>")
        sys.exit(2)
