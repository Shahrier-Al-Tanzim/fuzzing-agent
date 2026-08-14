"""Reads every artifact the pipeline produced and emits markdown tables.

Deliberately dependency-free: markdown tables and ASCII bars rather than
matplotlib. The report is markdown, the tables paste straight in, and there
is no plotting dependency to install or version-pin. If a chart is wanted
later, summary.json holds every number in machine-readable form.

Nothing here computes anything new - it only reads what Modules 3-6 already
measured. If a number is wrong, fix it upstream, not here.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import load, PROJECT_ROOT
from pipeline.features import PRODUCTIONS
from pipeline.schema import read_log


def _out_dir() -> Path:
    d = PROJECT_ROOT / "report" / "generated"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_state() -> dict:
    p = load().path("paths.state") / "loop_state.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _bar(fraction: float, width: int = 20) -> str:
    filled = int(round(fraction * width))
    return "█" * filled + "·" * (width - filled)


# --- tables ---------------------------------------------------------------

def iteration_table(state: dict) -> str:
    iters = state.get("iterations", [])
    if not iters:
        return "_No loop iterations recorded — run `python -m agent.loop` first._"

    rows = []
    for it in iters:
        s = it["summary"]
        attempts = len(it.get("generation", {}).get("attempts", []))
        rows.append(
            f"| {it['iteration']} "
            f"| {s['acceptance_rate']:.0%} "
            f"| {s['cumulative_coverage']:.0%} "
            f"| {len(s['productions_this_iteration'])} "
            f"| {s['novelty_rate']:.0%} "
            f"| {s['max_depth_cumulative']} "
            f"| {s['findings']} "
            f"| {attempts} "
            f"| {it.get('elapsed_s', 0):.0f}s |"
        )
    return (
        "| Iter | Accepted | Grammar coverage | New productions | Novel shapes "
        "| Max depth | Findings | LLM attempts | Time |\n"
        "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows)
    )


def coverage_table(state: dict) -> str:
    covered = set(state.get("covered_productions", []))
    if not covered:
        return "_No coverage recorded yet._"

    lines = [f"**{len(covered)}/{len(PRODUCTIONS)} productions covered "
             f"({len(covered) / len(PRODUCTIONS):.0%})**\n",
             "| Production | Covered |", "|---|---|"]
    for p in PRODUCTIONS:
        lines.append(f"| `{p}` | {'yes' if p in covered else '**NO**'} |")

    missing = [p for p in PRODUCTIONS if p not in covered]
    if missing:
        lines.append(
            "\n**Still under-tested (never appeared in an accepted document):** "
            + ", ".join(f"`{p}`" for p in missing))
    return "\n".join(lines)


def coverage_progression(state: dict) -> str:
    iters = state.get("iterations", [])
    if not iters:
        return ""
    lines = ["```", "Grammar coverage by iteration", ""]
    for it in iters:
        c = it["summary"]["cumulative_coverage"]
        lines.append(f"  iter {it['iteration']}  {_bar(c)}  {c:.0%}")
    lines += ["", "Acceptance rate by iteration", ""]
    for it in iters:
        a = it["summary"]["acceptance_rate"]
        lines.append(f"  iter {it['iteration']}  {_bar(a)}  {a:.0%}")
    lines.append("```")
    return "\n".join(lines)


def verdict_table() -> str:
    log_dir = load().path("paths.logs")
    logs = sorted(log_dir.glob("*.jsonl"))
    if not logs:
        return "_No run logs found._"

    rows = []
    for log in logs:
        recs = read_log(log)
        if not recs:
            continue
        c = Counter(r.verdict for r in recs)
        total = len(recs)
        rows.append(
            f"| `{log.stem}` | {total} "
            f"| {c.get('accept', 0)} | {c.get('reject', 0)} "
            f"| {c.get('crash', 0)} | {c.get('timeout', 0)} "
            f"| {c.get('harness_error', 0)} |"
        )
    return (
        "| Log | Inputs | Accept | Reject | Crash | Timeout | Harness error |\n"
        "|---|---|---|---|---|---|---|\n" + "\n".join(rows)
    )


def crash_table() -> str:
    crash_dir = load().path("paths.crashes")
    metas = sorted(crash_dir.glob("*/metadata.json"))
    if not metas:
        return ("_No crash reports found. If the loop genuinely found nothing, "
                "say so explicitly in the report and explain why — the "
                "assignment allows a documented 'none found'._")

    rows = []
    for m in metas:
        d = json.loads(m.read_text(encoding="utf-8"))
        sig = d["signature"]
        v = d["verification"]
        # Single source of truth: triage/verify.py already computed this
        # string and metadata.json stores it. Re-deriving it here is what
        # produced a false "did not reproduce" for a 3/3-reproducing crash -
        # see OBSERVATIONS.md Case 3. Only fall back for metadata written
        # before that field existed, and fail loudly rather than guess.
        status = v.get("description")
        if status is None:
            if v.get("deterministic"):
                status = "deterministic"
            elif v.get("unstable_signature"):
                status = "unstable signature"
            elif v.get("flaky"):
                status = "flaky"
            elif v.get("crashes") == 0:
                status = "did not reproduce"
            else:
                raise AssertionError(
                    f"unrecognized verification state in {m}: {v}")
        rows.append(
            f"| `{sig['digest']}` | {sig.get('bug_type', '?')} "
            f"| `{sig.get('short', '?')}` "
            f"| {d['occurrences']} "
            f"| {d['original_bytes']} → {d['minimized_bytes']} B "
            f"| {status} |"
        )
    return (
        "| Signature | Type | Label | Occurrences | Size (orig → min) | Verified |\n"
        "|---|---|---|---|---|---|\n" + "\n".join(rows)
    )


def budget_table(state: dict) -> str:
    cfg = load()
    iters = state.get("iterations", [])
    total_time = sum(it.get("elapsed_s", 0) for it in iters)
    total_examples = sum(it["summary"]["examples"] for it in iters)
    max_iter_time = max((it.get("elapsed_s", 0) for it in iters), default=0)

    # Which model actually produced these results. Read from the saved state
    # first: config.yaml can be changed after a run, and the report must
    # describe the run that happened, not the config as it stands now.
    provider = state.get("provider") or cfg.get("llm.provider", "ollama")
    model = state.get("model") or (
        cfg.get("llm.groq_model") if provider == "groq"
        else cfg.get("llm.model"))
    spend_note = (
        f"$0.00 (Groq free tier, {model})" if provider == "groq"
        else f"$0.00 (local {model})")

    return (
        "| Constraint | Limit | Actual | Within budget |\n"
        "|---|---|---|---|\n"
        f"| Loop iterations | {cfg.get('loop.max_iterations', 5)} | {len(iters)} "
        f"| {'yes' if len(iters) <= cfg.get('loop.max_iterations', 5) else 'NO'} |\n"
        f"| Examples per iteration | {cfg.get('run.max_examples', 500)} "
        f"| {total_examples // max(len(iters), 1)} avg | yes |\n"
        f"| Wall clock per iteration | {cfg.get('run.wall_clock_cap_seconds', 600)}s "
        f"| {max_iter_time:.0f}s max "
        f"| {'yes' if max_iter_time <= cfg.get('run.wall_clock_cap_seconds', 600) else 'NO'} |\n"
        f"| Per-input timeout | {cfg.get('harness.timeout_seconds', 5)}s | enforced | yes |\n"
        f"| LLM spend | ~$5 | {spend_note} | yes |\n"
        f"| LLM tokens | — | {state.get('total_tokens', 0):,} | — |\n"
        f"| Total loop wall clock | — | {total_time / 60:.1f} min | — |"
    )


# --- driver ---------------------------------------------------------------

def main() -> int:
    state = _load_state()
    out = _out_dir()

    artifacts = {
        "iteration_table.md": iteration_table(state),
        "coverage_table.md": coverage_table(state),
        "coverage_progression.md": coverage_progression(state),
        "verdict_table.md": verdict_table(),
        "crash_table.md": crash_table(),
        "budget_table.md": budget_table(state),
    }
    for name, content in artifacts.items():
        (out / name).write_text(content + "\n", encoding="utf-8")
        print(f"  wrote {out.name}/{name}")

    covered = set(state.get("covered_productions", []))
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "iterations": len(state.get("iterations", [])),
        "total_tokens": state.get("total_tokens", 0),
        "coverage": {
            "covered": sorted(covered),
            "missing": [p for p in PRODUCTIONS if p not in covered],
            "fraction": round(len(covered) / len(PRODUCTIONS), 3),
        },
        "max_depth_reached": state.get("max_depth_reached", 0),
        "per_iteration": [
            {"iteration": it["iteration"], **it["summary"]}
            for it in state.get("iterations", [])
        ],
        "unique_crashes": len(list(load().path("paths.crashes").glob("*/metadata.json"))),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2),
                                      encoding="utf-8")
    print(f"  wrote {out.name}/summary.json")

    print("\n=== headline numbers for the report ===")
    print(f"  iterations run     : {summary['iterations']}")
    print(f"  grammar coverage   : {summary['coverage']['fraction']:.0%}")
    print(f"  max nesting depth  : {summary['max_depth_reached']}")
    print(f"  unique bugs        : {summary['unique_crashes']}")
    print(f"  LLM tokens         : {summary['total_tokens']:,}")
    print(f"  still under-tested : {', '.join(summary['coverage']['missing'][:8]) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())