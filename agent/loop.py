"""The agentic loop: seed, run, summarize, refine, stop.

Budget enforcement is explicit and logged, because the assignment grades
"judgment under a budget":

  * loop.max_iterations       - 5 (iteration 0 is the seed)
  * run.max_examples          - 500 per iteration
  * run.wall_clock_cap_seconds- 600 per iteration, a backstop for a
                                pathological strategy, not a normal limit

Failure policy: if refinement produces nothing valid after all retries, the
loop keeps the previous iteration's strategy and continues rather than
aborting. A wasted iteration is a normal event regardless of which model is
generating - Groq's larger model fails less often than qwen2.5-coder:7b did
(see OBSERVATIONS.md Case 1/2), but "less often" is not "never," and losing
four good iterations to one bad generation would be the worse outcome
either way.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone

from hypothesis import HealthCheck, given, settings

from agent.coverage import LoopState
from agent.extract import extract_python
from agent.groq_client import GroqClient
from agent.ollama_client import OllamaClient, resolve_base_url
from agent.prompts import SYSTEM_PROMPT, build_refine_prompt, build_seed_prompt
from agent.strategy_store import (load_strategy_code, load_strategy_object,
                                  save_strategy)
from agent.summarize import render_feedback, summarize_iteration
from agent.validator import validate_strategy
from pipeline.config import load
from pipeline.features import extract_features
from pipeline.runner import HarnessRunner, RunLogger
from pipeline.schema import Verdict

RETRY_HEADER = """\
Your previous reply was rejected by an automated validator.

VALIDATOR ERROR:
{error}

Fix exactly that problem. Reply again with only one ```python block."""


def _generate(client: OllamaClient | GroqClient, prompt: str, iteration: int,
              max_attempts: int) -> tuple[str | None, dict]:
    """Prompt → validated code. Retries with the validator error quoted back."""
    attempts: list[dict] = []
    base = prompt
    for attempt in range(1, max_attempts + 1):
        resp = client.generate(prompt, system=SYSTEM_PROMPT)
        code = extract_python(resp.text)
        result = validate_strategy(code or "", probe=True)
        attempts.append({
            "attempt": attempt, "ok": result.ok, "stage": result.stage,
            "error": result.error[:300], "tokens": resp.total_tokens,
            "seconds": resp.duration_s, "stats": result.stats,
        })
        print(f"    attempt {attempt}: "
              f"{'PASS' if result.ok else 'FAIL ' + result.stage} "
              f"({resp.total_tokens} tok, {resp.duration_s}s)")
        if result.ok:
            save_strategy(iteration, code, accepted=True, attempt=attempt,
                          meta={"attempts": attempts, "stats": result.stats})
            return code, {"attempts": attempts, "stats": result.stats}
        if code:
            save_strategy(iteration, code, accepted=False, attempt=attempt)
        prompt = base + "\n\n" + RETRY_HEADER.format(error=result.feedback)
    return None, {"attempts": attempts, "stats": {}}


def run_iteration(iteration: int, strategy, state: LoopState) -> tuple[list, int]:
    """Run one strategy for max_examples, logging every record."""
    cfg = load()
    max_examples = cfg.get("run.max_examples", 500)
    wall_cap = cfg.get("run.wall_clock_cap_seconds", 600)

    # RunLogger appends - correct for Module 3's baseline runs, wrong here:
    # re-running this same iteration must replace its log, not mix a new
    # strategy's records in with a previous strategy's (see OBSERVATIONS.md
    # Case 4 - iteration_00.jsonl held 185 records from two different
    # strategies before this fix). Each iteration's log represents exactly
    # one strategy's run.
    log_path = load().path("paths.logs") / f"iteration_{iteration:02d}.jsonl"
    if log_path.exists():
        log_path.unlink()

    runner = HarnessRunner(iteration=iteration)
    records: list = []
    novel = 0
    started = time.perf_counter()
    index = 0

    with RunLogger(f"iteration_{iteration:02d}") as log:

        @given(strategy)
        @settings(
            max_examples=max_examples,
            deadline=None,
            database=None,
            suppress_health_check=[HealthCheck.too_slow,
                                   HealthCheck.data_too_large,
                                   HealthCheck.filter_too_much],
        )
        def check(text: str) -> None:
            nonlocal index, novel
            if time.perf_counter() - started > wall_cap:
                return
            rec = runner.run(text, example_index=index)
            index += 1
            rec.features = extract_features(text)
            if state.observe(rec.features,
                             accepted=rec.verdict == Verdict.ACCEPT.value):
                novel += 1
            records.append(rec)
            log.write(rec)

        check()

    return records, novel


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the agentic refinement loop.")
    ap.add_argument("--iterations", type=int, default=None,
                    help="override loop.max_iterations")
    ap.add_argument("--resume", action="store_true",
                    help="continue from saved state instead of starting fresh")
    ap.add_argument("--provider", choices=["ollama", "groq"], default=None,
                    help="which LLM backend to use "
                         "(default: llm.provider in config.yaml)")
    args = ap.parse_args()

    cfg = load()
    n_iters = args.iterations or cfg.get("loop.max_iterations", 5)
    max_attempts = cfg.get("llm.max_attempts", 4)
    provider = args.provider or cfg.get("llm.provider", "ollama")

    # Same provider switch as agent/seed.py (Module 4) - a 5-iteration loop
    # is exactly where a provider choice matters most, so this must not
    # silently default back to Ollama regardless of config.yaml.
    if provider == "groq":
        print("Provider: Groq (remote)")
        client = GroqClient()
    else:
        print(f"Ollama: {resolve_base_url()}")
        client = OllamaClient()
    state = LoopState.load_or_new() if args.resume else LoopState()
    state.provider = provider
    state.model = client.model
    start_at = len(state.iterations) if args.resume else 0

    current_code: str | None = (
        load_strategy_code(start_at - 1) if start_at else None)

    for iteration in range(start_at, n_iters):
        print(f"\n{'=' * 62}\n=== iteration {iteration}/{n_iters - 1}\n{'=' * 62}")
        t0 = time.perf_counter()

        # --- generate (seed on 0, refine after) ---
        if iteration == 0 or current_code is None:
            print("  generating seed strategy from grammar...")
            prompt = build_seed_prompt()
        else:
            print("  refining previous strategy from feedback...")
            feedback = render_feedback(state.iterations[-1]["summary"], state)
            prompt = build_refine_prompt(current_code, feedback, iteration - 1)

        code, gen_meta = _generate(client, prompt, iteration, max_attempts)

        if code is None:
            print("  !! generation failed; reusing previous strategy")
            if current_code is None:
                print("  !! no previous strategy to fall back on - stopping")
                return 1
            save_strategy(iteration, current_code, accepted=True,
                          meta={"note": "reused: generation failed"})
        else:
            current_code = code

        # --- run ---
        configured_max = cfg.get('run.max_examples', 500)
        print(f"  running up to {configured_max} examples...")
        strategy = load_strategy_object(iteration)
        records, novel = run_iteration(iteration, strategy, state)
        if len(records) < configured_max:
            # Hypothesis can stop well short of max_examples with no error
            # at all - e.g. a near-impossible .filter() exhausting its
            # retry budget (OBSERVATIONS.md Case 4). The old version of this
            # print always showed the configured cap regardless of what
            # actually ran, which hid that finding until someone counted
            # the JSONL log lines by hand.
            print(f"  !! only {len(records)}/{configured_max} examples "
                  "actually ran - Hypothesis stopped early (a strict "
                  ".filter() is the usual cause; see OBSERVATIONS.md Case 4)")
        else:
            print(f"  ran {len(records)} examples")

        # --- summarize ---
        summary = summarize_iteration(records, state, novel)
        state.iterations.append({
            "iteration": iteration,
            "summary": summary,
            "generation": gen_meta,
            "elapsed_s": round(time.perf_counter() - t0, 1),
            "at": datetime.now(timezone.utc).isoformat(),
        })
        state.total_tokens = client.total_tokens
        state.save()

        print(f"  accepted    : {summary['acceptance_rate']:.0%}")
        print(f"  coverage    : {summary['cumulative_coverage']:.0%} "
              f"(+{len(summary['productions_this_iteration'])} this run)")
        print(f"  novelty     : {summary['novelty_rate']:.0%}")
        print(f"  max depth   : {summary['max_depth_cumulative']}")
        print(f"  findings    : {summary['findings']}")
        print(f"  elapsed     : {state.iterations[-1]['elapsed_s']}s")

        _write_iteration_summary(iteration, summary, state)

    # --- final report data ---
    print(f"\n{'=' * 62}\n=== loop complete\n{'=' * 62}")
    for it in state.iterations:
        s = it["summary"]
        print(f"  iter {it['iteration']}: accept {s['acceptance_rate']:.0%}  "
              f"cov {s['cumulative_coverage']:.0%}  "
              f"depth {s['max_depth_cumulative']:>3}  "
              f"findings {s['findings']}")
    print(f"\nusage: {json.dumps(client.usage_summary())}")
    print(f"state: {state.save()}")
    return 0


def _write_iteration_summary(iteration: int, summary: dict,
                             state: LoopState) -> None:
    d = load().path("paths.state")
    d.mkdir(parents=True, exist_ok=True)
    (d / f"iteration_{iteration:02d}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    (d / f"iteration_{iteration:02d}_feedback.md").write_text(
        render_feedback(summary, state), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())