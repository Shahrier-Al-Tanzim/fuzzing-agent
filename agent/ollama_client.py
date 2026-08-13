"""Ollama HTTP client with WSL host discovery and failure-aware retries.

Two problems this solves:

1. *Where is Ollama?* It runs on Windows; this code runs in WSL. The Windows
   host is reachable at the WSL default-route gateway, which changes across
   reboots. `resolve_base_url()` probes candidates and caches the winner.

2. *The model is 7B.* Every call goes through `generate()`, which returns raw
   text; the retry loop that judges that text lives in `validator.py`, not
   here. This module deliberately does not know what a "good" answer is.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from pipeline.config import load

_CACHED_BASE_URL: str | None = None


def _wsl_gateway_ip() -> str | None:
    """The Windows host's address as seen from WSL2 (default-route gateway)."""
    try:
        out = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=5,
        ).stdout.split()
        if "via" in out:
            return out[out.index("via") + 1]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def _responds(base_url: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def resolve_base_url(force: bool = False) -> str:
    """Find a reachable Ollama. Cached, because probing costs a round trip.

    Order: $OLLAMA_BASE_URL, the configured value (if not "auto"), the WSL
    gateway, then localhost. First one that answers /api/tags wins.
    """
    global _CACHED_BASE_URL
    if _CACHED_BASE_URL and not force:
        return _CACHED_BASE_URL

    configured = str(load().get("llm.base_url", "auto")).strip()

    candidates: list[str] = []
    if os.environ.get("OLLAMA_BASE_URL"):
        candidates.append(os.environ["OLLAMA_BASE_URL"].rstrip("/"))
    if configured and configured.lower() != "auto":
        candidates.append(configured.rstrip("/"))
    gw = _wsl_gateway_ip()
    if gw:
        candidates.append(f"http://{gw}:11434")
    candidates.append("http://localhost:11434")

    seen: set[str] = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        if _responds(url):
            _CACHED_BASE_URL = url
            return url

    raise ConnectionError(
        "Cannot reach Ollama. Tried:\n  " + "\n  ".join(seen) + "\n\n"
        "On Windows (PowerShell):  setx OLLAMA_HOST \"0.0.0.0\"\n"
        "then fully quit and reopen Ollama from the system tray.\n"
        "Verify from WSL:\n"
        "  curl http://$(ip route show default | awk '{print $3}'):11434/api/tags"
    )


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_s: float = 0.0
    model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class OllamaClient:
    """Thin wrapper over /api/generate.

    Token counts are recorded on every call because the assignment requires
    reporting spend. Ollama is free, but "0 dollars, N tokens" is the honest
    version of that line in the report.
    """

    model: str = ""
    temperature: float = 0.3
    num_ctx: int = 16384
    timeout_s: int = 300
    total_tokens: int = 0
    calls: int = 0
    _history: list[LLMResponse] = field(default_factory=list)

    def __post_init__(self) -> None:
        cfg = load()
        self.model = self.model or cfg.get("llm.model", "qwen2.5-coder:7b")
        self.temperature = cfg.get("llm.temperature", self.temperature)
        self.num_ctx = cfg.get("llm.num_ctx", self.num_ctx)
        self.timeout_s = cfg.get("llm.request_timeout_seconds", self.timeout_s)

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
        }
        if system:
            payload["system"] = system

        base = resolve_base_url()
        req = urllib.request.Request(
            f"{base}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - started

        out = LLMResponse(
            text=body.get("response", ""),
            prompt_tokens=body.get("prompt_eval_count", 0),
            completion_tokens=body.get("eval_count", 0),
            duration_s=round(elapsed, 2),
            model=self.model,
        )
        self.total_tokens += out.total_tokens
        self.calls += 1
        self._history.append(out)
        return out

    def usage_summary(self) -> dict:
        return {
            "model": self.model,
            "calls": self.calls,
            "total_tokens": self.total_tokens,
            "total_seconds": round(sum(h.duration_s for h in self._history), 1),
            "usd_cost": 0.0,  # local model; recorded explicitly for the report
        }