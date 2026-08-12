"""Drives the baseline strategies through the harness and reports.

Note what this does NOT do: it does not assert. A @given test that asserts
"no crash" stops at the first failure and invokes the shrinker, which is
exactly right for Module 6 but wrong here - the baseline needs a full
census of 500 examples to produce an acceptance rate. Shrinking is Module
6's job; this module only proves the plumbing.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pipeline.baseline_strategy import BASELINE_STRATEGIES
from pipeline.config import load
from pipeline.runner import HarnessRunner, RunLogger
from pipeline.schema import Verdict


def run_strategy(name: str, strategy: st.SearchStrategy, max_examples: int,
                 wall_cap: float) -> Counter:
    runner = HarnessRunner(iteration=0)
    counts: Counter = Counter()
    started = time.perf_counter()
    index = 0

    with RunLogger(f"baseline_{name}") as log:

        @given(strategy)
        @settings(
            max_examples=max_examples,
            deadline=None,                     # subprocess timing is ours to bound
            database=None,                     # no cross-run example reuse in the baseline
            suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
        )
        def check(text: str) -> None:
            nonlocal index
            if time.perf_counter() - started > wall_cap:
                return                          # wall-clock backstop
            record = runner.run(text, example_index=index)
            index += 1
            counts[record.verdict] += 1
            log.write(record)

        check()

    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the baseline pipeline check.")
    ap.add_argument("--strategy", choices=[*BASELINE_STRATEGIES, "all"], default="all")
    ap.add_argument("--max-examples", type=int, default=None)
    args = ap.parse_args()

    cfg = load()
    max_examples = args.max_examples or cfg.get("run.max_examples", 500)
    wall_cap = cfg.get("run.wall_clock_cap_seconds", 600)

    names = list(BASELINE_STRATEGIES) if args.strategy == "all" else [args.strategy]
    results: dict[str, Counter] = {}

    for name in names:
        print(f"\n=== {name} ({max_examples} examples) ===")
        t0 = time.perf_counter()
        counts = run_strategy(name, BASELINE_STRATEGIES[name], max_examples, wall_cap)
        elapsed = time.perf_counter() - t0
        results[name] = counts

        total = sum(counts.values()) or 1
        for verdict in Verdict:
            n = counts.get(verdict.value, 0)
            if n:
                print(f"  {verdict.value:<14} {n:>5}  ({n / total:5.1%})")
        print(f"  {'elapsed':<14} {elapsed:>5.1f}s "
              f"({elapsed / total * 1000:.0f} ms/example)")

    print("\n=== pipeline health ===")
    ok = True

    accepted = results.get("keyvalue_lines", Counter()).get("accept", 0)
    if "keyvalue_lines" in results:
        if accepted == 0:
            print("  FAIL  keyvalue_lines never accepted - runner or harness is broken")
            ok = False
        else:
            print(f"  ok    keyvalue_lines accepted {accepted} inputs "
                  "(ACCEPT path works)")

    rejected = sum(c.get("reject", 0) for c in results.values())
    if rejected == 0:
        print("  FAIL  nothing was ever rejected - REJECT path untested")
        ok = False
    else:
        print(f"  ok    {rejected} rejections observed (REJECT path works)")

    harness_errors = sum(c.get("harness_error", 0) for c in results.values())
    if harness_errors:
        print(f"  WARN  {harness_errors} harness errors (exit 64) - investigate")

    findings = sum(c.get("crash", 0) + c.get("timeout", 0) for c in results.values())
    if findings:
        print(f"  NOTE  {findings} crashes/timeouts from the *baseline* - "
              "unexpected this early, and worth saving")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())