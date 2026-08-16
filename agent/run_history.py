"""Permanent, append-only record of every LLM generation attempt, every
iteration's measured results, and every run's outcome - across every
invocation of both agent/seed.py and agent/loop.py.

Why this exists: neither pipeline/logs/*.jsonl (deliberately cleared before
each iteration re-runs - see OBSERVATIONS.md Case 4) nor
agent/state/loop_state.json (fully overwritten by each fresh `agent.loop`
invocation) preserve history across separate runs. This file is the fix:
records are appended, never cleared, never overwritten.

Lives in logs/ at the project root - NOT the same as pipeline/logs/, which
is a different, older, disposable per-run example log that gets cleared
before each iteration re-runs. logs/RUN_HISTORY.* is explicitly excepted
from .gitignore's `**/logs/*.jsonl` rule (see .gitignore's comment) so it
still gets committed and persists, despite also living in a folder named
"logs".

history/ (a separate folder, also at the project root) holds the original
RUN_HISTORY.jsonl/.md from before this file's rewrite - reconstructed after
the fact from old saved strategies (a "backfill"). logs/ only ever contains
records logged live, going forward.

Three kinds of record, one JSONL line each, all sharing a "run_id":
  * "attempt"          - one LLM generation try (as before)
  * "iteration_result" - the measured accept/coverage/novelty/depth/findings
                         once an iteration's strategy actually passed and ran
  * "run_complete"     - written at the end of a process invocation, ok=True
                         if all iterations finished, ok=False if it stopped
                         early (ran out of attempts, or the process itself
                         died - e.g. an API key hitting its rate limit
                         mid-run). Usually once per run_id, but a --resume
                         that continues the same run_id (see LoopState.run_id
                         in agent/coverage.py) appends another one when it
                         eventually finishes - rendering always uses the
                         LATEST record for a run_id's final status. If a
                         run_id never gets this record at all, rendering
                         treats it as failed/incomplete too -
                         a run that crashes hard enough to kill the process
                         doesn't get a chance to write one.

RUN_HISTORY.md is the human-readable view: grouped by run, then by
iteration within that run, with every attempt shown and the passing
iteration's metrics printed right after it. Fully regenerated from the
.jsonl on every write - the .jsonl stays flat and append-only (rewriting
the whole file on every single attempt would defeat the point of an
append-only log); the .md is derived, never hand-edited, and gets
overwritten the next time anything is logged.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.config import PROJECT_ROOT

LOGS_DIR = PROJECT_ROOT / "logs"
RUN_HISTORY_PATH = LOGS_DIR / "RUN_HISTORY.jsonl"
RUN_HISTORY_MD_PATH = LOGS_DIR / "RUN_HISTORY.md"


def _append(record: dict[str, Any]) -> None:
    record.setdefault("at", datetime.now(timezone.utc).isoformat())
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
    regenerate_markdown()


def get_next_run_id() -> int:
    """Highest run_id seen so far, plus one. 1 if nothing's logged yet."""
    if not RUN_HISTORY_PATH.exists():
        return 1
    max_run = 0
    for line in RUN_HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        run_id = json.loads(line).get("run_id")
        if isinstance(run_id, int):
            max_run = max(max_run, run_id)
    return max_run + 1


def log_attempt(*, run_id: int, source: str, iteration: int, attempt: int,
                ok: bool, stage: str, error: str, tokens: int,
                seconds: float, provider: str, model: str,
                stats: dict[str, Any] | None = None) -> None:
    """Append one generation attempt's outcome."""
    _append({
        "kind": "attempt",
        "run_id": run_id,
        "source": source,          # "seed" | "loop"
        "iteration": iteration,
        "attempt": attempt,
        "ok": ok,
        "stage": stage,
        "error": (error or "")[:300],
        "tokens": tokens,
        "seconds": seconds,
        "provider": provider,
        "model": model,
        "stats": stats or {},
    })


def log_iteration_result(*, run_id: int, iteration: int,
                         summary: dict[str, Any], elapsed_s: float) -> None:
    """Append one iteration's measured results, once its strategy passed
    and actually ran against the harness."""
    _append({
        "kind": "iteration_result",
        "run_id": run_id,
        "iteration": iteration,
        "accepted": summary.get("acceptance_rate"),
        "coverage": summary.get("cumulative_coverage"),
        "novelty": summary.get("novelty_rate"),
        "max_depth": summary.get("max_depth_cumulative"),
        "findings": summary.get("findings"),
        "examples": summary.get("examples"),
        "elapsed_s": elapsed_s,
    })


def log_run_complete(*, run_id: int, ok: bool, iterations_completed: int,
                     reason: str = "completed") -> None:
    """Append the final outcome of a run - ok=True only if every iteration
    finished. Call this from a finally block, not just the success path, so
    a run stopped partway still gets an explicit record instead of just
    trailing off with no explanation.

    `reason` distinguishes a real generation dead-end from everything else -
    the rendering only labels a run FAILED for "exhausted_attempts" (an
    iteration ran out of every attempt with no earlier strategy to fall
    back on) or "keyboard_interrupt" (the user chose to stop it). Any other
    reason (an unexpected error, or anything not otherwise classified)
    renders as STOPPED instead - iterations that already passed with real
    metrics aren't "failed" just because something else ended the run
    early.
    """
    _append({
        "kind": "run_complete",
        "run_id": run_id,
        "ok": ok,
        "iterations_completed": iterations_completed,
        "reason": reason,
    })


def regenerate_markdown() -> None:
    """Rebuild RUN_HISTORY.md from RUN_HISTORY.jsonl, grouped by run, then
    by iteration within that run - matching how the loop actually executes,
    not a flat chronological list."""
    if not RUN_HISTORY_PATH.exists():
        return
    records = [json.loads(line) for line in
              RUN_HISTORY_PATH.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    if not records:
        RUN_HISTORY_MD_PATH.write_text(
            "# Run History\n\nNo attempts logged yet.\n", encoding="utf-8")
        return

    by_run: dict[int, list[dict]] = {}
    for r in records:
        by_run.setdefault(r.get("run_id", 0), []).append(r)

    lines = [
        "# Run History",
        "",
        "**Auto-generated from `RUN_HISTORY.jsonl` — do not edit by hand,**"
        " this file is fully rewritten every time anything new is logged.",
        "One section per run, in order; within each run, one section per"
        " iteration, in order; every attempt shown, with the measured"
        " results printed right after whichever attempt passed.",
        "",
        f"**Total runs: {len(by_run)}**",
        "",
        "---",
        "",
    ]

    for run_id in sorted(by_run):
        entries = by_run[run_id]
        attempts = [e for e in entries if e.get("kind") == "attempt"]
        iter_results = {e["iteration"]: e for e in entries
                        if e.get("kind") == "iteration_result"}
        # A resumed run can log more than one "run_complete" record for the
        # same run_id - once when an earlier attempt died mid-way (e.g. an
        # uncaught exception on iteration 3), again when --resume later
        # actually finishes it. The LAST one reflects the true final
        # outcome; picking the first would keep showing the old crash
        # status forever even after the run genuinely completed.
        complete = next((e for e in reversed(entries)
                         if e.get("kind") == "run_complete"), None)
        reason = (complete or {}).get("reason", "unknown")

        if complete and complete.get("ok"):
            status = "✅ PASSED (all iterations completed)"
        elif reason == "exhausted_attempts":
            status = "❌ FAILED (ran out of attempts, no earlier strategy to fall back on)"
        elif reason == "keyboard_interrupt":
            status = "❌ FAILED (stopped by Ctrl+C)"
        else:
            # Anything else - an unexpected error, or the run_complete
            # record itself is missing entirely (process died hard enough
            # that even the finally block never ran) - is NOT a generation
            # failure. Iterations that already passed above are real,
            # valid results; only the two reasons above are worth calling
            # "failed" at the whole-run level.
            status = "⚠️ STOPPED (not a generation failure - see reason below)"
        lines.append(f"## Run {run_id} — {status}")
        lines.append("")

        by_iteration: dict[int, list[dict]] = {}
        for a in attempts:
            by_iteration.setdefault(a["iteration"], []).append(a)

        for iteration in sorted(by_iteration):
            iter_attempts = by_iteration[iteration]
            passed = sum(1 for a in iter_attempts if a["ok"])
            lines.append(f"### Iteration {iteration} — {passed}/{len(iter_attempts)} attempts passed")
            lines.append("")
            lines.append("| At (UTC) | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for a in iter_attempts:
                result = "PASS" if a["ok"] else "FAIL"
                err = (a.get("error") or "").replace("|", "\\|").replace("\n", " ")
                if len(err) > 90:
                    err = err[:90] + "…"
                at = (a.get("at") or "")[:19].replace("T", " ")
                lines.append(
                    f"| {at} | {a.get('attempt', '?')} | {result} "
                    f"| {a.get('stage', '?')} "
                    f"| {a.get('provider', '?')}/{a.get('model', '?')} "
                    f"| {a.get('tokens', 0)} | {a.get('seconds', 0)} | {err} |"
                )
            lines.append("")

            ir = iter_results.get(iteration)
            if ir:
                def pct(x): return f"{x:.0%}" if isinstance(x, (int, float)) else "?"
                lines.append(
                    f"**Result:** accepted {pct(ir.get('accepted'))} · "
                    f"coverage {pct(ir.get('coverage'))} · "
                    f"novelty {pct(ir.get('novelty'))} · "
                    f"max depth {ir.get('max_depth', '?')} · "
                    f"findings {ir.get('findings', '?')} · "
                    f"examples {ir.get('examples', '?')} · "
                    f"elapsed {ir.get('elapsed_s', '?')}s"
                )
                lines.append("")

        if not (complete and complete.get("ok")):
            reached = max(by_iteration) if by_iteration else -1
            reason_text = {
                "exhausted_attempts": "an iteration ran out of every attempt "
                    "with no earlier passing strategy to fall back on",
                "keyboard_interrupt": "stopped by Ctrl+C",
            }.get(reason, f"reason: {reason} (not a generation failure - "
                          "iterations shown above with a Result line "
                          "genuinely passed)")
            label = "**FAILED**" if reason in ("exhausted_attempts", "keyboard_interrupt") \
                else "**STOPPED**"
            where = (f"after iteration {reached}" if reached >= 0
                    else "before any iteration completed")
            lines.append(f"{label} — stopped {where}. {reason_text}.")
            lines.append("")

        lines.append("---")
        lines.append("")

    RUN_HISTORY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
