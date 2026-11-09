"""The ONLY module in eval/ that may call a model (I2). Used by the LLM attacker (E1) and the quality judge (E3).

- Official `anthropic` SDK, imported lazily. It is not in requirements.txt yet (request sent to the integrator);
  without it, or without credentials, calls are served from the replay cache or raise LLMUnavailable,
  and callers skip the LLM-based measurement. The deterministic attackers never need this module.
- Every response is cached under eval/cache/llm/<sha256>.json so `make eval` can replay offline (I8 spirit)
  and results are reproducible. EVAL_REPLAY=1 forces cache-only.
- Model: EVAL_ATTACKER_MODEL, else CLOUD_MODEL, else claude-opus-5-5.
- Only synthetic data is ever sent (I1): transcripts built by eval/ from fixtures, never a real profile.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

CACHE = pathlib.Path(__file__).resolve().parent / "cache" / "llm"
DEFAULT_MODEL = "claude-opus-5-5"


class LLMUnavailable(RuntimeError):
    """No SDK, no credentials, or replay mode with a cache miss."""


def model_name() -> str:
    return os.environ.get("EVAL_ATTACKER_MODEL") or os.environ.get("CLOUD_MODEL") or DEFAULT_MODEL


def _key(model: str, system: str, prompt: str) -> str:
    return hashlib.sha256(json.dumps([model, system, prompt]).encode()).hexdigest()


def _cache_get(k: str) -> str | None:
    f = CACHE / f"{k}.json"
    return json.loads(f.read_text())["text"] if f.exists() else None


def _cache_put(k: str, model: str, text: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"{k}.json").write_text(json.dumps({"model": model, "text": text}))


def complete(prompt: str, system: str = "", effort: str = "medium") -> str:
    """One request, returns the text. Cache first; live call only when not in replay mode."""
    model = model_name()
    k = _key(model, system, prompt)
    hit = _cache_get(k)
    if hit is not None:
        return hit
    if os.environ.get("EVAL_REPLAY") == "1":
        raise LLMUnavailable("replay mode and no cached response")
    try:
        import anthropic
    except ImportError as e:
        raise LLMUnavailable("anthropic SDK not installed (requested from integrator)") from e
    try:
        client = anthropic.Anthropic()
        kwargs = dict(model=model, max_tokens=16000, output_config={"effort": effort},
                      messages=[{"role": "user", "content": prompt}])
        if system:
            kwargs["system"] = system
        if model == DEFAULT_MODEL:
            # server-side refusal fallback: routes a declined request to a fallback model by category
            resp = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        else:
            resp = client.messages.create(**kwargs)
    except anthropic.AuthenticationError as e:
        raise LLMUnavailable("no valid credentials") from e
    except anthropic.APIConnectionError as e:
        raise LLMUnavailable("network unavailable") from e
    if resp.stop_reason == "refusal":
        raise LLMUnavailable(f"model declined (category={getattr(resp.stop_details, 'category', None)})")
    text = "".join(b.text for b in resp.content if b.type == "text")
    _cache_put(k, model, text)
    return text


def complete_json(prompt: str, system: str = "", effort: str = "medium") -> dict:
    """complete() and parse the first JSON object in the reply."""
    text = complete(prompt, system, effort)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
    return json.loads(text[start:end + 1])
