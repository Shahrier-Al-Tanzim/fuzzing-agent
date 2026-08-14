"""Confirms a reproducer crashes deterministically before it is reported.

The assignment requires this explicitly: "Re-run each minimized reproducer
once, standalone, against the pinned build to confirm it deterministically
reproduces the crash before including it in your report."

We run it N times (default 3), not once. A crash that fires 1 time in 3 is a
real and interesting finding, but reporting it as deterministic would be
wrong - so the count is recorded either way.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.config import load
from pipeline.runner import HarnessRunner
from triage.signature import parse_signature


@dataclass
class VerifyResult:
    runs: int
    crashes: int
    signature_matches: int
    verdicts: list[str]

    @property
    def deterministic(self) -> bool:
        return self.crashes == self.runs and self.signature_matches == self.runs

    @property
    def flaky(self) -> bool:
        return 0 < self.crashes < self.runs

    @property
    def unstable_signature(self) -> bool:
        """Crashed on every run, but not every crash matched the expected
        digest. A real, reliably-reproducing crash whose exact stack trace
        isn't perfectly stable run to run - distinct from `flaky`, which is
        about whether it crashes at all, not whether its signature holds.
        Seen in practice near a recursion-depth threshold, the same kind of
        run-to-run sensitivity minimize.py's step counts show."""
        return self.crashes == self.runs and self.signature_matches < self.runs

    def describe(self) -> str:
        if self.deterministic:
            return f"deterministic ({self.crashes}/{self.runs} runs crashed)"
        if self.unstable_signature:
            return (f"crashed every run ({self.crashes}/{self.runs}) but "
                    f"signature unstable ({self.signature_matches}/{self.runs} "
                    "matched)")
        if self.flaky:
            return f"FLAKY ({self.crashes}/{self.runs} runs crashed)"
        if self.crashes == 0:
            return f"DID NOT REPRODUCE (0/{self.runs})"
        # Every named state above is proven exhaustive ONLY under the
        # invariant signature_matches <= crashes <= runs, which verify()
        # currently guarantees but nothing enforces long-term. A prior
        # version of this method silently fell through to "DID NOT
        # REPRODUCE" for a state that didn't actually mean that - fail
        # loudly instead of guessing if that ever happens again.
        raise AssertionError(
            "VerifyResult matched no known state - the state model is "
            f"incomplete. runs={self.runs} crashes={self.crashes} "
            f"signature_matches={self.signature_matches}")


def verify(text: str, expected_digest: str | None = None) -> VerifyResult:
    cfg = load()
    n = cfg.get("triage.verify_runs", 3)
    runner = HarnessRunner(iteration=-3)

    crashes = matches = 0
    verdicts: list[str] = []
    for _ in range(n):
        rec = runner.run(text)
        verdicts.append(rec.verdict)
        if rec.is_finding:
            crashes += 1
            if expected_digest is None:
                matches += 1
            else:
                sig = parse_signature(rec.stderr, rec.signal)
                if sig and sig.digest == expected_digest:
                    matches += 1
    return VerifyResult(runs=n, crashes=crashes,
                        signature_matches=matches, verdicts=verdicts)
