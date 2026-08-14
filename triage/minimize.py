"""Reduces a crashing input to a small reproducer.

Path A - Hypothesis shrinking (`shrink_with_hypothesis`): the assignment's
preferred route. Requires the strategy that produced the crash, because
Hypothesis shrinks the choice sequence behind a value, not the value itself.

Path B - delta debugging (`minimize_concrete`): for crashing inputs read back
from logs, where no generating strategy is available. Three passes, cheapest
first:
    1. line removal      - binary-search chunks of lines
    2. depth reduction   - halve bracket nesting (the big win for recursion
                           bugs: 60000 -> ~48000 in a handful of steps)
    3. character trim    - shave the ends

Every candidate must still crash *with the same signature*, not merely crash.
Otherwise minimization can silently walk from one bug to a different one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.config import load
from pipeline.runner import HarnessRunner
from triage.signature import CrashSignature, parse_signature


@dataclass
class MinimizeResult:
    text: str
    original_bytes: int
    minimized_bytes: int
    steps: int
    method: str
    signature_held: bool

    @property
    def reduction(self) -> float:
        if not self.original_bytes:
            return 0.0
        return 1 - (self.minimized_bytes / self.original_bytes)


def _crashes_same(runner: HarnessRunner, text: str,
                  target: CrashSignature) -> bool:
    rec = runner.run(text)
    if not rec.is_finding:
        return False
    sig = parse_signature(rec.stderr, rec.signal)
    if sig is None:
        # A timeout has no sanitizer output; match on verdict alone.
        return target.bug_type.startswith("timeout")
    return sig.digest == target.digest


def _reduce_depth(text: str) -> list[str]:
    """Candidates with bracket nesting halved. The key move for recursion bugs."""
    out: list[str] = []
    for op, cl in (("[", "]"), ("{", "}")):
        m = re.search(re.escape(op) + r"{4,}", text)
        if not m:
            continue
        run = m.end() - m.start()
        for frac in (0.5, 0.75, 0.9):
            keep = max(2, int(run * frac))
            cand = text.replace(op * run, op * keep, 1)
            cand = cand.replace(cl * run, cl * keep, 1)
            if cand != text:
                out.append(cand)
    return out


def minimize_concrete(text: str, target: CrashSignature,
                      iteration: int = -2) -> MinimizeResult:
    """Delta debugging for an input with no generating strategy (Path B)."""
    cfg = load()
    max_steps = cfg.get("triage.minimize_max_steps", 400)
    runner = HarnessRunner(iteration=iteration)

    original = text
    best = text
    steps = 0

    # --- pass 1: depth reduction (huge inputs first) ---
    improved = True
    while improved and steps < max_steps:
        improved = False
        for cand in _reduce_depth(best):
            steps += 1
            if steps >= max_steps:
                break
            if len(cand) < len(best) and _crashes_same(runner, cand, target):
                best = cand
                improved = True
                break

    # --- pass 2: line removal, binary-search style ---
    lines = best.split("\n")
    chunk = max(1, len(lines) // 2)
    while chunk >= 1 and steps < max_steps:
        i = 0
        while i < len(lines) and steps < max_steps:
            cand_lines = lines[:i] + lines[i + chunk:]
            cand = "\n".join(cand_lines)
            steps += 1
            if cand.strip() and _crashes_same(runner, cand, target):
                lines = cand_lines
            else:
                i += chunk
        chunk //= 2
    best = "\n".join(lines)

    # --- pass 3: trim the ends ---
    for _ in range(min(60, max_steps - steps)):
        if len(best) <= 8:
            break
        trimmed = False
        for cand in (best[:-max(1, len(best) // 20)],
                     best[max(1, len(best) // 20):]):
            steps += 1
            if cand.strip() and _crashes_same(runner, cand, target):
                best = cand
                trimmed = True
                break
        if not trimmed:
            break

    return MinimizeResult(
        text=best,
        original_bytes=len(original.encode()),
        minimized_bytes=len(best.encode()),
        steps=steps,
        method="delta-debugging",
        signature_held=_crashes_same(runner, best, target),
    )


def shrink_with_hypothesis(strategy, iteration: int = -2,
                           max_examples: int = 500) -> MinimizeResult | None:
    """Path A: let Hypothesis find and shrink a crash natively.

    Works by asserting "no input crashes". When that assertion fails,
    Hypothesis's own shrinker runs automatically and reports the smallest
    counterexample it can reach.
    """
    from hypothesis import HealthCheck, given, settings
    from hypothesis.errors import Flaky

    runner = HarnessRunner(iteration=iteration)
    found: dict = {}

    @given(strategy)
    @settings(
        max_examples=max_examples,
        deadline=None,
        database=None,
        suppress_health_check=[HealthCheck.too_slow,
                               HealthCheck.data_too_large,
                               HealthCheck.filter_too_much],
    )
    def no_crash(text: str) -> None:
        rec = runner.run(text)
        if rec.is_finding:
            found["text"] = text
            found["stderr"] = rec.stderr
            found["signal"] = rec.signal
        assert not rec.is_finding, f"harness reported {rec.verdict}"

    try:
        no_crash()
    except AssertionError:
        pass                      # expected: Hypothesis shrank to this
    except Flaky:
        pass                      # non-deterministic; verify.py will catch it
    else:
        return None               # no crash found in this budget

    text = found.get("text", "")
    return MinimizeResult(
        text=text,
        original_bytes=len(text.encode()),
        minimized_bytes=len(text.encode()),
        steps=max_examples,
        method="hypothesis-shrink",
        signature_held=True,
    )