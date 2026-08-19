"""Stage 1+2: ask the model for a strategy, validate it, retry with feedback.

The retry loop is the deliverable. Each failed attempt appends the validator's
message to the next prompt, so the model is told exactly what it got wrong
instead of being asked again cold.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from agent.extract import extract_python
from agent.gemini_client import GeminiClient
from agent.groq_client import GroqClient
from agent.ollama_client import OllamaClient, resolve_base_url
from agent.prompts import SYSTEM_PROMPT, build_seed_prompt
from agent.run_history import get_next_run_id, log_attempt, log_run_complete
from agent.strategy_store import save_strategy
from agent.validator import validate_strategy
from pipeline.config import load

RETRY_HEADER = """\
Your previous reply was rejected by an automated validator.

VALIDATOR ERROR:
{error}

Fix exactly that problem. Reply again with only one ```python block that
satisfies the output contract."""


def generate_validated_strategy(iteration: int = 0, probe: bool = True,
                                verbose: bool = True, provider: str = "ollama"):
    cfg = load()
    max_attempts = cfg.get("llm.max_attempts", 4)
    if provider == "gemini":
        client = GeminiClient()
    elif provider == "groq":
        client = GroqClient()
    else:
        client = OllamaClient()

    base_prompt = build_seed_prompt()
    prompt = base_prompt
    attempts_log: list[dict] = []

    # Shares the same run-numbering sequence as agent.loop - both write to
    # logs/RUN_HISTORY.jsonl, so "run N" is just "the Nth invocation of
    # either script," in order. finally ensures a crashed/interrupted seed
    # attempt still gets an explicit FAILED record.
    run_id = get_next_run_id()
    completed_ok = False
    try:
        for attempt in range(1, max_attempts + 1):
            if verbose:
                print(f"\n--- attempt {attempt}/{max_attempts} "
                      f"(prompt {len(prompt)} chars) ---")

            resp = client.generate(prompt, system=SYSTEM_PROMPT)
            _save_transcript(iteration, attempt, prompt, resp.text)

            code = extract_python(resp.text)
            result = validate_strategy(code or "", probe=probe)

            attempts_log.append({
                "attempt": attempt,
                "ok": result.ok,
                "stage": result.stage,
                "error": result.error,
                "stats": result.stats,
                "tokens": resp.total_tokens,
                "seconds": resp.duration_s,
            })
            log_attempt(run_id=run_id, source="seed", iteration=iteration,
                        attempt=attempt, ok=result.ok, stage=result.stage,
                        error=result.error, tokens=resp.total_tokens,
                        seconds=resp.duration_s, provider=provider,
                        model=client.model, stats=result.stats)

            if verbose:
                print(f"    tokens={resp.total_tokens} time={resp.duration_s}s")
                if result.ok:
                    print(f"    PASS  {result.stats}")
                else:
                    print(f"    FAIL  [{result.stage}] {result.error[:180]}")

            if result.ok:
                path = save_strategy(
                    iteration, code, accepted=True, attempt=attempt,
                    meta={
                        "iteration": iteration,
                        "attempts": attempts_log,
                        "stats": result.stats,
                        "usage": client.usage_summary(),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    run_id=run_id,
                )
                if verbose:
                    print(f"\nsaved: {path}")
                completed_ok = True
                return result, path, client

            if code:
                save_strategy(iteration, code, accepted=False, attempt=attempt)
            prompt = base_prompt + "\n\n" + RETRY_HEADER.format(error=result.feedback)

        return None, None, client
    finally:
        log_run_complete(run_id=run_id, ok=completed_ok,
                         iterations_completed=1 if completed_ok else 0)


def main() -> int:
    cfg = load()
    ap = argparse.ArgumentParser(description="Seed a strategy from the grammar.")
    ap.add_argument("--iteration", type=int, default=0)
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the harness acceptance gate (faster, weaker)")
    ap.add_argument("--provider", choices=["ollama", "groq", "gemini"], default=None,
                    help="which LLM backend to use "
                         "(default: llm.provider in config.yaml)")
    args = ap.parse_args()
    provider = args.provider or cfg.get("llm.provider", "ollama")

    if provider == "gemini":
        print("Provider: Gemini (remote)")
    elif provider == "groq":
        print("Provider: Groq (remote)")
    else:
        print(f"Ollama: {resolve_base_url()}")
    result, path, client = generate_validated_strategy(
        iteration=args.iteration, probe=not args.no_probe,
        provider=provider)

    print("\n=== usage ===")
    print(json.dumps(client.usage_summary(), indent=2))

    if result is None:
        print("\nFAILED: no attempt produced a valid strategy.")
        print("Rejected candidates are saved in agent/strategies/ - read them.")
        return 1

    print(f"\nOK: validated strategy at {path}")
    print(f"    acceptance rate : {result.stats.get('acceptance_rate')}")
    print(f"    uses recursion  : {result.stats.get('uses_recursion')}")
    if not result.stats.get("uses_recursion"):
        print("    WARNING: no st.recursive/@composite found. The assignment "
              "grades this. Re-run, or refine in Module 5.")
    return 0


def _save_transcript(iteration: int, attempt: int, prompt: str, reply: str) -> None:
    d = load().path("paths.prompts")
    d.mkdir(parents=True, exist_ok=True)
    (d / f"iter_{iteration:02d}_attempt{attempt}.md").write_text(
        f"# Iteration {iteration}, attempt {attempt}\n\n"
        f"## Prompt\n\n````\n{prompt}\n````\n\n"
        f"## Reply\n\n````\n{reply}\n````\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    sys.exit(main())