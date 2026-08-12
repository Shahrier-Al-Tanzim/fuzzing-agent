"""The one record type every run produces, and every later module reads.

One JSON object per line (JSONL): appendable during a run, streamable when
reading, and survives a crashed run with everything up to that point intact
- which a single big JSON array would not.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    """What happened to one input.

    ACCEPT and REJECT are the only non-findings. Note that TIMEOUT is
    separate from CRASH in the data even though the assignment counts it as
    a crash for grading - keeping them distinct in the log lets the report
    say how many of each, and collapsing them later is trivial while
    splitting them later is impossible.
    """
    ACCEPT = "accept"       # exit 0 - library parsed it
    REJECT = "reject"       # exit 2 - well-formed rejection
    CRASH = "crash"         # signal or sanitizer abort
    TIMEOUT = "timeout"     # exceeded per-run limit; counts as a crash
    HARNESS_ERROR = "harness_error"  # exit 64 - our bug, not the library's

    @property
    def is_finding(self) -> bool:
        return self in (Verdict.CRASH, Verdict.TIMEOUT)


@dataclass
class RunRecord:
    """Result of feeding exactly one input to the harness."""

    # --- identity ---
    run_id: str                     # sha256 of input, first 16 hex chars
    iteration: int                  # which agentic-loop iteration (0 = baseline)
    example_index: int              # position within that iteration's run

    # --- the input ---
    input_text: str
    input_bytes: int
    input_sha256: str

    # --- the outcome ---
    verdict: str                    # a Verdict value
    exit_code: int | None           # None if killed by signal or timed out
    signal: int | None              # POSIX signal number, if any
    duration_ms: float

    # --- diagnostics ---
    stderr: str = ""                # truncated; full text kept for findings
    reject_message: str = ""        # parsed from the harness's "REJECT: ..."
    sanitizer_type: str = ""        # e.g. "heap-buffer-overflow"

    # --- structural features (filled by Module 5) ---
    features: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "RunRecord":
        return cls(**json.loads(line))

    @property
    def is_finding(self) -> bool:
        return Verdict(self.verdict).is_finding


def read_log(path) -> list[RunRecord]:
    """Read a JSONL log, skipping blank and malformed lines.

    Tolerant by design: a run killed mid-write leaves a partial final line,
    and losing one record should not cost the whole log.
    """
    records: list[RunRecord] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(RunRecord.from_json(line))
            except (json.JSONDecodeError, TypeError):
                continue
    return records