"""Turns one iteration's run log into compact feedback for the model.

Budget-aware: the refine prompt must hold the grammar, the current strategy
source, and this summary inside num_ctx (16384). So this stays under roughly
1500 characters - counts and directives, never raw inputs.
"""
from __future__ import annotations

from collections import Counter

from agent.coverage import LoopState
from pipeline.config import load
from pipeline.features import PRODUCTIONS
from pipeline.schema import RunRecord, Verdict


def summarize_iteration(records: list[RunRecord], state: LoopState,
                        novel_count: int) -> dict:
    """Numeric summary. Kept separate from prose so the report can chart it."""
    cfg = load()
    total = len(records) or 1
    verdicts = Counter(r.verdict for r in records)
    accepted = [r for r in records if r.verdict == Verdict.ACCEPT.value]

    depths = [r.features.get("max_depth", 0) for r in accepted if r.features]
    prods_this_iter: set[str] = set()
    for r in accepted:
        prods_this_iter.update(r.features.get("productions", []))

    reject_msgs = [r.reject_message for r in records
                   if r.verdict == Verdict.REJECT.value and r.reject_message]

    return {
        "examples": total,
        "acceptance_rate": round(len(accepted) / total, 3),
        "verdicts": dict(verdicts),
        "novelty_rate": round(novel_count / total, 3),
        "productions_this_iteration": sorted(prods_this_iter),
        "cumulative_coverage": round(state.coverage_fraction, 3),
        "missing_productions": state.missing_productions,
        "max_depth_this_iteration": max(depths, default=0),
        "max_depth_cumulative": state.max_depth_reached,
        "mean_bytes": round(
            sum(r.input_bytes for r in records) / total, 1),
        "findings": sum(1 for r in records if r.is_finding),
        "top_rejects": Counter(reject_msgs).most_common(
            cfg.get("features.top_reject_messages", 5)),
    }


def render_feedback(summary: dict, state: LoopState) -> str:
    """The text actually pasted into the refine prompt."""
    cfg = load()
    max_missing = cfg.get("features.max_missing_shown", 8)
    floor = cfg.get("loop.acceptance_rate_floor", 0.20)

    missing = summary["missing_productions"][:max_missing]
    rejects = "\n".join(
        f"  - {n:>4}x  {msg[:70]}" for msg, n in summary["top_rejects"]
    ) or "  (none)"

    crash_line = (
        f"{len(state.crash_signatures)} unique crash signature(s) so far: "
        f"{', '.join(state.crash_signatures[:3])}"
        if state.crash_signatures else
        "No crashes found yet by any iteration."
    )

    # --- directives: the part that actually changes the model's output ---
    directives: list[str] = []
    if summary["acceptance_rate"] < floor:
        directives.append(
            f"RAISE ACCEPTANCE FIRST. Only {summary['acceptance_rate']:.0%} of "
            f"documents parsed (floor {floor:.0%}). Fix the errors listed above "
            "before adding new features.")
    for p in missing[:5]:
        directives.append(
            f"Generate `{p}` - it has never appeared in an accepted document.")
    if summary["max_depth_cumulative"] < 12:
        directives.append(
            f"Increase nesting depth. Best reached so far is "
            f"{summary['max_depth_cumulative']}; aim for 12+ by raising the "
            "`max_leaves`/depth limit in your st.recursive call.")
    if summary["novelty_rate"] < 0.25:
        directives.append(
            f"Increase structural variety - only {summary['novelty_rate']:.0%} "
            "of documents had a shape not already seen. Vary which constructs "
            "co-occur, not just their values.")
    if not directives:
        directives.append(
            "Coverage and depth are healthy. Push further into rare "
            "combinations: deeply nested inline tables inside array-of-tables, "
            "and extreme numeric/string values in those positions.")

    return f"""\
## Results from the previous strategy ({summary['examples']} documents)

Parser outcomes : {summary['verdicts']}
Accepted        : {summary['acceptance_rate']:.0%}
Novel shapes    : {summary['novelty_rate']:.0%}
Grammar coverage: {summary['cumulative_coverage']:.0%} of \
{len(PRODUCTIONS)} tracked productions
Max nest depth  : {summary['max_depth_this_iteration']} this run, \
{summary['max_depth_cumulative']} cumulative
Mean size       : {summary['mean_bytes']} bytes
{crash_line}

Most common parser rejections:
{rejects}

NEVER generated in an accepted document:
  {', '.join(missing) if missing else '(all tracked productions covered)'}

## What to change, in priority order
{chr(10).join(f'{i}. {d}' for i, d in enumerate(directives, 1))}
"""