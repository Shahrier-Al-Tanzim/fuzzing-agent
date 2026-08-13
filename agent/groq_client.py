"""Groq API client — alternative to OllamaClient for testing whether a
larger, remotely-hosted model avoids the API-hallucination failures
documented in OBSERVATIONS.md Case 1.

Same public shape as OllamaClient (generate() -> LLMResponse,
usage_summary()), so this is a drop-in swap for whatever code constructs
the client — nothing in validator.py, extract.py, prompts.py, or seed.py
needs to change to use this instead.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from pipeline.config import load

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_RATE_LIMIT_RETRIES = 5
DEFAULT_RATE_LIMIT_WAIT_S = 20.0

_RETRY_MS_RE = re.compile(r"try again in (\d+(?:\.\d+)?)(m?s)", re.IGNORECASE)


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
class GroqClient:
    """Chat-completions client for Groq's OpenAI-compatible API.

    Requires GROQ_API_KEY in the environment (see .env — gitignored, never
    commit it). Free tier: no cost at time of writing, but rate-limited
    rather than unlimited — a 429 means "rate limited," not "broken."
    """

    model: str = ""
    temperature: float = 0.3
    timeout_s: int = 120
    total_tokens: int = 0
    calls: int = 0
    _history: list[LLMResponse] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Run:  source .env\n"
                "then re-run this command in the same shell."
            )
        self.model = self.model or load().get(
            "llm.groq_model", "llama-3.3-70b-versatile")

    def _wait_seconds(self, exc: urllib.error.HTTPError, detail: str) -> float:
        """How long Groq wants us to wait, from whatever it told us.

        Prefers the Retry-After header (seconds); falls back to parsing
        "try again in Xs"/"Xms" out of the error body; falls back to a safe
        default if neither is present. A small buffer is added either way -
        cutting it exactly to the reported time tends to still get a 429.
        """
        header = exc.headers.get("Retry-After") if exc.headers else None
        if header:
            try:
                return float(header) + 1.0
            except ValueError:
                pass
        m = _RETRY_MS_RE.search(detail)
        if m:
            value, unit = float(m.group(1)), m.group(2).lower()
            return (value / 1000.0 if unit == "ms" else value) + 1.0
        return DEFAULT_RATE_LIMIT_WAIT_S

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                # Groq's API is behind Cloudflare, which blocks the default
                # urllib User-Agent (Cloudflare error 1010) - any normal
                # value avoids the block.
                "User-Agent": "fuzzing-agent/1.0",
            },
        )

        started = time.perf_counter()
        body = None
        for retry in range(MAX_RATE_LIMIT_RETRIES + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")
                if exc.code == 401:
                    raise RuntimeError(
                        "Groq rejected the API key (401 Unauthorized). "
                        "Check GROQ_API_KEY in .env."
                    ) from exc
                if exc.code == 429:
                    if retry >= MAX_RATE_LIMIT_RETRIES:
                        raise RuntimeError(
                            f"Groq free-tier rate limit hit (429) after "
                            f"{MAX_RATE_LIMIT_RETRIES} retries: {detail[:200]}"
                        ) from exc
                    wait = self._wait_seconds(exc, detail)
                    print(f"    [groq] rate limited (429), waiting {wait:.0f}s "
                          f"before retry {retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"Groq API error {exc.code}: {detail[:300]}") from exc
        elapsed = time.perf_counter() - started

        text = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})

        out = LLMResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
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
            "usd_cost": 0.0,  # free tier at time of writing
        }
