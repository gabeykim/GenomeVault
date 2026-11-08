"""Local model client. Integrator-owned. Localhost only (I2)."""
import os
from urllib.parse import urlparse
import httpx

BASE = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:11434")
assert urlparse(BASE).hostname in {"127.0.0.1", "localhost", "::1"}, "local_llm must stay on localhost (I2)"
MODEL = os.environ.get("LOCAL_LLM_MODEL", "set-me")  # P10: chosen with Lenovo engineers

def generate(prompt: str, system: str = "") -> str:
    r = httpx.post(f"{BASE}/api/generate", json={"model": MODEL, "prompt": prompt, "system": system, "stream": False, "think": False}, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "")
