"""Drive the Mode-1 crash-hunting strategies through the harness.

Unlike pipeline/run_baseline.py (which never asserts, to collect a full
census), this DOES assert "no crash" inside the @given test - so when a
generated input crashes tomlc99, Hypothesis's shrinker kicks in automatically
and minimizes the input to the smallest crashing example, exactly as the
assignment's Step 5.4 asks ("use Hypothesis's shrinking - it runs
automatically when a @given-wrapped test fails").

Because depth is an explicit integer parameter (see strategies.py), the
shrinker converges the crash toward each range's minimum - so the reported
reproducer is the smallest/most-parseable crashing depth for that construct.

Every run (including every shrink step) is logged to pipeline/logs/ via the
same RunLogger the rest of the pipeline uses, so crashes found here are picked
up by `python -m triage.run_triage` with NO --extra needed - i.e. they are
genuinely *loop/generator-found*, not hand-fed.

A crash is logged with a *parseable* stack when possible (run_for_parseable_
crash), since triage reads stored stderr from the logs without re-running -
so a frameless log record would bucket the crash into the wrong ("unparsed")
signature. See pipeline/runner.run_for_parseable_crash.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.errors import Flaky

from pipeline.crash_hunt_strategy import CRASH_HUNT_STRATEGIES
from pipeline.config import load
from pipeline.runner import HarnessRunner, RunLogger, run_for_parseable_crash
from pipeline.schema import Verdict


class CrashFound(AssertionError):
    """Raised inside the @given test when the harness reports a crash/timeout,
    so Hypothesis treats it as a failing example and shrinks it."""


def hunt(name: str, strategy: st.SearchStrategy, max_examples: int,
         wall_cap: float) -> tuple[Counter, str | None]:
    """Run one crash-hunt campaign. Returns (verdict counts, minimal crashing
    input if one was found and shrunk, else None)."""
    runner = HarnessRunner(iteration=-3)  # -3 marks crash-hunt runs in logs
    counts: Counter = Counter()
    started = time.perf_counter()
    minimal_crash: dict[str, str | None] = {"text": None}

    with RunLogger(f"crashhunt_{name}") as log:

        @given(strategy)
        @settings(
            max_examples=max_examples,
            deadline=None,          # giant inputs are legitimately slow
            database=None,          # no cross-run reuse; each run rediscovers
            suppress_health_check=[HealthCheck.too_slow,
                                   HealthCheck.data_too_large,
                                   HealthCheck.filter_too_much],
        )
        def check(text: str) -> None:
            if time.perf_counter() - started > wall_cap:
                return              # wall-clock backstop; don't fail the test
            # Retry a crash for a parseable stack so the LOGGED record buckets
            # to the right signature (triage reads log stderr without re-running).
            rec = run_for_parseable_crash(runner, text)
            counts[rec.verdict] += 1
            log.write(rec)
            if rec.is_finding:
                # Remember the smallest crashing input Hypothesis has shown us;
                # it shrinks toward the range minimum, so the last one recorded
                # here is the minimal reproducer.
                minimal_crash["text"] = text
                raise CrashFound(
                    f"{name}: tomlc99 {rec.verdict} on a {len(text)}-byte input")

        try:
            check()
        except CrashFound:
            # Expected: a crash was found and shrunk. The exception carries the
            # minimal failing example; minimal_crash["text"] holds it too.
            pass
        except Flaky:
            # Hypothesis saw an input crash once but not on replay - genuinely
            # possible for a deep overflow sitting right at the stack threshold
            # (see info.md "unstable signature"). Report it honestly rather
            # than pretending it's clean or letting it abort the whole hunt.
            print(f"  !! {name}: crash was flaky under Hypothesis replay "
                  "(threshold-sensitive overflow) - see logs")

    return counts, minimal_crash["text"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Hunt for crashes with deliberately extreme inputs.")
    ap.add_argument("--campaign",
                    choices=[*CRASH_HUNT_STRATEGIES, "all"], default="all")
    ap.add_argument("--max-examples", type=int, default=25,
                    help="upper bound on tries before giving up on a campaign; "
                         "a reliably-crashing campaign stops at the first crash "
                         "then shrinks. Default 25 (well under the 500 cap).")
    args = ap.parse_args()

    cfg = load()
    wall_cap = cfg.get("run.wall_clock_cap_seconds", 600)

    names = (list(CRASH_HUNT_STRATEGIES) if args.campaign == "all"
             else [args.campaign])
    any_crash = False

    for name in names:
        print(f"\n=== hunting: {name} ===")
        t0 = time.perf_counter()
        counts, minimal = hunt(name, CRASH_HUNT_STRATEGIES[name],
                               args.max_examples, wall_cap)
        elapsed = time.perf_counter() - t0

        total = sum(counts.values()) or 1
        for verdict in Verdict:
            n = counts.get(verdict.value, 0)
            if n:
                print(f"  {verdict.value:<14} {n:>4}  ({n / total:5.0%})")
        print(f"  {'elapsed':<14} {elapsed:>4.1f}s")

        findings = counts.get("crash", 0) + counts.get("timeout", 0)
        if findings and minimal is not None:
            any_crash = True
            print(f"  >> CRASH FOUND, shrunk to {len(minimal)} bytes. "
                  "Logged to pipeline/logs/ - run `python -m triage.run_triage`.")
        elif findings:
            any_crash = True
            print(f"  >> {findings} crash(es) logged (shrink incomplete).")
        else:
            print("  -- no crash in this campaign.")

    print("\n=== done ===")
    if any_crash:
        print("  Crashes are in pipeline/logs/crashhunt_*.jsonl.")
        print("  Triage them (no --extra needed):  python -m triage.run_triage")
    else:
        print("  No crashes found this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
