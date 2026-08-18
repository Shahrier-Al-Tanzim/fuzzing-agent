"""Turns one iteration's run log into compact feedback for the model.

Budget-aware: the refine prompt must hold the grammar, the current strategy
source, and this summary inside num_ctx (16384 tokens, ~4 chars/token). This
stays under roughly 2200 characters worst-case (~550 tokens, still a small
slice of the budget) - counts and directives, never raw inputs. The ceiling
moved up from an earlier ~1500 to fit the depth-escalation directive (see
DEPTH_TARGETS below), which has to teach a concrete biasing technique once
depth is asked to go past a few hundred - a flat "aim for N" doesn't work
past that point (see the directive's own comment), so it costs more
characters than the rest of the directives combined.
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


# Geometric, not linear, depth escalation - a flat "aim for 12+" can never
# close the gap to a real stack-overflow threshold (tomlc99's confirmed bugs
# need ~48k-105k levels; see planning/planning-crash-hunting.md and
# grammar/early_findings/). Indexed by how many iterations have already
# completed (len(state.iterations)), so the target ramps up hard across the
# 5-iteration budget instead of asking for the same modest number every time.
DEPTH_TARGETS = [12, 200, 4_000, 30_000, 90_000]


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
    depth_target = DEPTH_TARGETS[min(len(state.iterations),
                                     len(DEPTH_TARGETS) - 1)]
    if summary["max_depth_cumulative"] < depth_target:
        if depth_target <= 200:
            directives.append(
                f"Increase nesting depth. Best reached so far is "
                f"{summary['max_depth_cumulative']}; aim for {depth_target}+ "
                "by raising the `max_leaves`/depth limit in your "
                "st.recursive call.")
        else:
            # Past a few hundred, a balanced/uniform recursion choice cannot
            # reach this target - Hypothesis's own bias toward short lists
            # collapses depth long before then. Ask for the specific
            # technique, not just a bigger number.
            directives.append(
                f"PUSH DEPTH MUCH FURTHER. Best reached so far is "
                f"{summary['max_depth_cumulative']}; target {depth_target}+ "
                "this time - a real bug in tomlc99 needs tens of thousands "
                "of nesting levels to trigger, so a balanced 1-in-3 "
                "one_of(value(), array(), inline_table()) choice will never "
                "get there (it decays to near-zero probability of nesting "
                "that deep). Add a SEPARATE strategy variant that recurses "
                "with heavy bias toward itself - e.g. repeat the recursive "
                "option several times in one_of() so it is drawn far more "
                "often than scalars, or thread an explicit depth counter "
                "through draw() (incrementing it on every recursive call - "
                "not just declaring one) and only stop recursing once that "
                "counter passes a high threshold. Combine both generation "
                "styles with st.one_of() so the balanced style still covers "
                "the grammar broadly while the biased style hunts depth.")
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