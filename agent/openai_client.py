"""OpenAI API client — provider option alongside Ollama, Groq, and Gemini.

Reads OPENAI_API_KEY from environment (.env).
Uses OpenAI's standard chat completions endpoint (https://api.openai.com/v1/chat/completions).

Maintains the standard client interface:
- generate(prompt, system) -> LLMResponse
- usage_summary() -> dict
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from pipeline.config import PROJECT_ROOT, load

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MAX_RATE_LIMIT_RETRIES = 5
DEFAULT_RATE_LIMIT_WAIT_S = 15.0

_RETRY_AFTER_RE = re.compile(r"try again in (\d+(?:\.\d+)?)(m?s)", re.IGNORECASE)


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
class OpenAIClient:
    """Chat completions client for OpenAI API.

    Requires OPENAI_API_KEY in environment (.env).
    Default model configured via config.yaml (llm.openai_model) or passed directly.
    """

    model: str = ""
    temperature: float = 0.3
    timeout_s: int = 0
    total_tokens: int = 0
    calls: int = 0
    _history: list[LLMResponse] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            env_path = PROJECT_ROOT / ".env"
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("export OPENAI_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("OPENAI_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Check OPENAI_API_KEY in .env or run: source .env"
            )
        self.model = self.model or load().get(
            "llm.openai_model", "gpt-4o-mini")
        self.timeout_s = self.timeout_s or load().get(
            "llm.request_timeout_seconds", 300)

    def _wait_seconds(self, exc: urllib.error.HTTPError, detail: str) -> float:
        header = exc.headers.get("Retry-After") if exc.headers else None
        if header:
            try:
                return float(header) + 1.0
            except ValueError:
                pass
        m = _RETRY_AFTER_RE.search(detail)
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
        }
        if not any(k in self.model.lower() for k in ("luna", "sol", "terra", "o1", "o3")):
            payload["temperature"] = self.temperature
        req = urllib.request.Request(
            OPENAI_API_URL,
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
                        f"OpenAI rejected the API key ({exc.code}). "
                        "Check OPENAI_API_KEY in .env."
                    ) from exc
                if exc.code == 429:
                    if retry >= MAX_RATE_LIMIT_RETRIES:
                        raise RuntimeError(
                            f"OpenAI rate limit hit (429) after "
                            f"{MAX_RATE_LIMIT_RETRIES} retries: {detail[:200]}"
                        ) from exc
                    wait = self._wait_seconds(exc, detail)
                    print(f"    [openai] rate limited (429), waiting {wait:.0f}s "
                          f"before retry {retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                    time.sleep(wait)
                    continue
                if exc.code in (500, 502, 503, 504):
                    if retry >= MAX_RATE_LIMIT_RETRIES:
                        raise RuntimeError(
                            f"OpenAI server error ({exc.code}) persisted "
                            f"after {MAX_RATE_LIMIT_RETRIES} retries: "
                            f"{detail[:200]}"
                        ) from exc
                    wait = self._wait_seconds(exc, detail)
                    print(f"    [openai] server error ({exc.code}), waiting "
                          f"{wait:.0f}s before retry "
                          f"{retry + 1}/{MAX_RATE_LIMIT_RETRIES}...")
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"OpenAI API error {exc.code}: {detail[:300]}") from exc
            except (TimeoutError, urllib.error.URLError) as exc:
                if retry >= MAX_RATE_LIMIT_RETRIES:
                    raise RuntimeError(
                        f"OpenAI did not respond within {self.timeout_s}s, "
                        f"after {MAX_RATE_LIMIT_RETRIES} retries: {exc}"
                    ) from exc
                print(f"    [openai] request timed out, retrying "
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
        total_prompt = sum(h.prompt_tokens for h in self._history)
        total_completion = sum(h.completion_tokens for h in self._history)
        
        # Calculate cost based on model
        if "mini" in self.model:
            input_rate = 0.15 / 1_000_000
            output_rate = 0.60 / 1_000_000
        elif "4o" in self.model:
            input_rate = 2.50 / 1_000_000
            output_rate = 10.00 / 1_000_000
        else: # gpt-5 / gpt-5.4 flagship tier
            input_rate = 2.50 / 1_000_000
            output_rate = 10.00 / 1_000_000
            
        usd_cost = round((total_prompt * input_rate) + (total_completion * output_rate), 4)

        return {
            "model": self.model,
            "calls": self.calls,
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_tokens": self.total_tokens,
            "total_seconds": round(sum(h.duration_s for h in self._history), 1),
            "usd_cost": usd_cost,
        }
