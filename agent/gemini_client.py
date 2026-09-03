"""Gemini API client — third provider option alongside Ollama and Groq.

Added after Groq deprecated llama-3.3-70b-versatile (see config.yaml's
comment) and every currently-active Groq model turned out to share the
same 8,000 tokens-per-minute free-tier ceiling - too small for this
project's ~8,000-9,500 token prompts once rules 9-17 accumulated. Gemini's
free tier gives roughly 250,000 TPM (confirmed live, not just documented),
comfortably clearing that wall.

Uses Gemini's OpenAI-compatible endpoint (generativelanguage.googleapis.com
/v1beta/openai/...) rather than its native API, specifically so the
request/response shape - and therefore this whole file - matches
GroqClient almost exactly: same LLMResponse, same generate()/
usage_summary() interface, so it's a drop-in swap for whatever code
constructs the client, same as GroqClient already is for OllamaClient.

Confirmed live: Gemini is also a reasoning model (like gpt-oss-120b), but
keeps reasoning in its own opaque field, never mixed into the visible
`content` - unlike Qwen models, which interleave <think> tags directly
into content. So no extra stripping logic is needed here, same as Groq.
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

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
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
class GeminiClient:
    """Chat-completions client for Gemini's OpenAI-compatible API.

    Requires GEMINI_API_KEY in the environment (see .env — gitignored,
    never commit it). Free tier at time of writing: no cost, ~250,000
    tokens/minute — verified live against the real prompt sizes this
    project sends, not just read from docs.
    """

    model: str = ""
    temperature: float = 0.3
    timeout_s: int = 0
    total_tokens: int = 0
    calls: int = 0
    _history: list[LLMResponse] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Run:  source .env\n"
                "then re-run this command in the same shell."
            )
        self.model = self.model or load().get(
            "llm.gemini_model", "gemini-3.6-flash")
        # 120s was too tight for this model's reasoning phase on longer
        # refine prompts (iteration 2 of Run 15 timed out mid-response and
        # crashed the loop with an uncaught TimeoutError). Shares
        # llm.request_timeout_seconds with the Ollama client.
        self.timeout_s = self.timeout_s or load().get(
            "llm.request_timeout_seconds", 300)

    def _wait_seconds(self, exc: urllib.error.HTTPError, detail: str) -> float:
        """How long Gemini wants us to wait, from whatever it told us.

        Same logic as GroqClient - prefers Retry-After, falls back to
        parsing "try again in Xs"/"Xms" from the body, falls back to a
        safe default. Not yet confirmed which of these Gemini actually
        sends on a real 429; kept generic so any of the three still works.
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
            GEMINI_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
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
                if exc.code in (401, 403):
                    raise RuntimeError(
                        f"Gemini rejected the API key ({exc.code}). "
                        "Check GEMINI_API_KEY in .env."
                    ) from exc
                if exc.code == 429:
                    if retry >= MAX_RATE_LIMIT_RETRIES:
                        raise RuntimeError(
                            f"Gemini free-tier rate limit hit (429) after "
                            f"{MAX_RATE_LIMIT_RETRIES} retries: {detail[:200]}"
                        ) from exc
                    wait = self._wait_seconds(exc, detail)
                    print(f"    [gemini] rate limited (429), waiting {wait:.0f}s "
                          f"before retry {retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                    time.sleep(wait)
                    continue
                if exc.code == 404:
                    raise RuntimeError(
                        f"Gemini model `{self.model}` not found - it may "
                        "have been retired. Full error: "
                        f"{detail[:300]}") from exc
                if exc.code in (500, 502, 503, 504):
                    # Google's own message calls this transient ("usually
                    # temporary, try again later") - worth retrying same as
                    # 429, not a fatal config/code problem.
                    if retry >= MAX_RATE_LIMIT_RETRIES:
                        raise RuntimeError(
                            f"Gemini server error ({exc.code}) persisted "
                            f"after {MAX_RATE_LIMIT_RETRIES} retries: "
                            f"{detail[:200]}"
                        ) from exc
                    wait = self._wait_seconds(exc, detail)
                    print(f"    [gemini] server error ({exc.code}), waiting "
                          f"{wait:.0f}s before retry "
                          f"{retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"Gemini API error {exc.code}: {detail[:300]}") from exc
            except (TimeoutError, urllib.error.URLError) as exc:
                if retry >= MAX_RATE_LIMIT_RETRIES:
                    raise RuntimeError(
                        f"Gemini did not respond within {self.timeout_s}s, "
                        f"after {MAX_RATE_LIMIT_RETRIES} retries: {exc}"
                    ) from exc
                print(f"    [gemini] request timed out, retrying "
                      f"{retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                continue
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
