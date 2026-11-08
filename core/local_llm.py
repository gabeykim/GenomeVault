"""Local model client. Integrator-owned. Localhost only (I2).

generate(prompt, system="", images=None, format=None, model=None) -> str
- images: base64-encoded images, for the vision model (D-029).
- format: "json" or a JSON schema dict, to force structured output.
- model: defaults to LOCAL_LLM_MODEL; pass VLM_MODEL for label photos.
Thinking is off for text calls ("think": False, D-028).
"""
import os
from typing import Optional, Union
from urllib.parse import urlparse

import httpx

BASE = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:11434")
assert urlparse(BASE).hostname in {"127.0.0.1", "localhost", "::1"}, "local_llm must stay on localhost (I2)"
MODEL = os.environ.get("LOCAL_LLM_MODEL", "set-me")      # D-028: qwen3:8b on the demo laptop
VLM_MODEL = os.environ.get("LOCAL_VLM_MODEL", "set-me")  # D-029: qwen2.5vl:7b for label photos


def generate(prompt: str, system: str = "", images: Optional[list[str]] = None,
             format: Optional[Union[str, dict]] = None, model: Optional[str] = None) -> str:
    body: dict = {"model": model or MODEL, "prompt": prompt, "system": system, "stream": False}
    if images:
        body["images"] = images
    else:
        body["think"] = False
    if format is not None:
        body["format"] = format
    r = httpx.post(f"{BASE}/api/generate", json=body, timeout=180)
    r.raise_for_status()
    return r.json().get("response", "")
