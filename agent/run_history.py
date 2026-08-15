"""Permanent, append-only record of every LLM generation attempt, ever made,
across every run of both agent/seed.py and agent/loop.py.

Why this exists: neither pipeline/logs/*.jsonl (deliberately cleared before
each iteration re-runs - see OBSERVATIONS.md Case 4) nor
agent/state/loop_state.json (fully overwritten by each fresh `agent.loop`
invocation) preserve attempt history across separate runs. Once a run
ended, its pass/fail detail was gone unless it happened to get written up
by hand in OBSERVATIONS.md. This file is the fix: one line appended per
attempt, never cleared, never overwritten, so "every run, logged" is
actually true going forward.

Lives in logs/ at the project root - NOT the same as pipeline/logs/, which
is a different, older, disposable per-run example log that gets cleared
before each iteration re-runs. logs/RUN_HISTORY.* is explicitly excepted
from .gitignore's `**/logs/*.jsonl` rule (see .gitignore's comment) so it
still gets committed and persists, despite also living in a folder named
"logs".

history/ (a separate folder, also at the project root) holds the original
RUN_HISTORY.jsonl/.md from before this file's rewrite - reconstructed after
the fact from old saved strategies (a "backfill"), and mixing that
reconstructed data with live entries was confusing. logs/ starts clean and
only ever contains attempts logged live, going forward, by this file.

RUN_HISTORY.md is a second, human-readable file kept in sync automatically:
every call to log_attempt() appends one line to the .jsonl (cheap, safe,
never rewrites what's already there) and then fully regenerates the .md
from the complete .jsonl, grouped by iteration. The .jsonl stays flat and
append-only on purpose - grouping it by iteration directly would mean
rewriting the whole file on every single attempt, which defeats the point
of an append-only log. The .md is the organized view; the .jsonl is the
ground truth it's rendered from. Never hand-edit RUN_HISTORY.md - it gets
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


def log_attempt(*, source: str, iteration: int, attempt: int, ok: bool,
                stage: str, error: str, tokens: int, seconds: float,
                provider: str, model: str,
                stats: dict[str, Any] | None = None) -> None:
    """Append one generation attempt's outcome, then regenerate the
    human-readable .md view. Append-only on the .jsonl side - never
    truncates or rewrites what's already there, matching RunLogger's
    per-line-flush approach so a killed process still leaves a complete,
    readable log."""
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
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
    }
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
    regenerate_markdown()


def regenerate_markdown() -> None:
    """Rebuild RUN_HISTORY.md from RUN_HISTORY.jsonl, grouped by iteration.

    Reads the whole .jsonl (small enough for a class project's scope that
    this is cheap even called after every single attempt) so the .md is
    always a complete, current rendering - never something that can drift
    out of sync with the .jsonl it's derived from.
    """
    if not RUN_HISTORY_PATH.exists():
        return
    records = [json.loads(line) for line in
              RUN_HISTORY_PATH.read_text(encoding="utf-8").splitlines()
              if line.strip()]

    by_iteration: dict[int, list[dict]] = {}
    for r in records:
        by_iteration.setdefault(r["iteration"], []).append(r)

    total_pass = sum(1 for r in records if r["ok"])
    lines = [
        "# Run History",
        "",
        "**Auto-generated from `RUN_HISTORY.jsonl` — do not edit by hand,**"
        " this file is fully rewritten every time a new attempt is logged.",
        "Every generation attempt, across every run of `agent.seed` and"
        " `agent.loop`, grouped by iteration, oldest attempt first within"
        " each group.",
        "",
        f"**Total: {total_pass}/{len(records)} attempts passed, across"
        f" {len(by_iteration)} distinct iteration numbers.**",
        "",
    ]

    for iteration in sorted(by_iteration):
        entries = by_iteration[iteration]
        passed = sum(1 for e in entries if e["ok"])
        lines.append(f"## Iteration {iteration} — {passed}/{len(entries)} attempts passed")
        lines.append("")
        lines.append("| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for e in entries:
            result = "PASS" if e["ok"] else "FAIL"
            err = (e.get("error") or "").replace("|", "\\|").replace("\n", " ")
            if len(err) > 90:
                err = err[:90] + "…"
            at = (e.get("at") or "")[:19].replace("T", " ")
            lines.append(
                f"| {at} | {e.get('source', '?')} | {e.get('attempt', '?')} "
                f"| {result} | {e.get('stage', '?')} "
                f"| {e.get('provider', '?')}/{e.get('model', '?')} "
                f"| {e.get('tokens', 0)} | {e.get('seconds', 0)} | {err} |"
            )
        lines.append("")

    RUN_HISTORY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
