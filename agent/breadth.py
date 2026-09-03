"""Cumulative grammar breadth and novelty bookkeeping across iterations.

"Breadth" here means: of the ~30 tracked TOML grammar productions
(pipeline/features.py's PRODUCTIONS), how many have appeared at least once
in an accepted generated document. It is computed by regex-matching our
OWN generated text, never by instrumenting tomlc99's binary - the
assignment forbids real code coverage of the target, and this metric is
not that; see OBSERVATIONS.md's terminology note.

State lives in agent/state/loop_state.json so a crashed or interrupted run
can be resumed without losing the breadth history - which, unlike the logs,
cannot be reconstructed after the fact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from pipeline.config import load
from pipeline.features import PRODUCTIONS


def _state_path() -> Path:
    d = load().path("paths.state")
    d.mkdir(parents=True, exist_ok=True)
    return d / "loop_state.json"


@dataclass
class LoopState:
    """Everything the loop must remember between iterations."""

    reached_productions: list[str] = field(default_factory=list)
    seen_signatures: list[str] = field(default_factory=list)
    max_depth_reached: int = 0
    crash_signatures: list[str] = field(default_factory=list)
    iterations: list[dict] = field(default_factory=list)
    total_tokens: int = 0
    # Which model actually produced this run. Recorded here rather than read
    # from config.yaml at report time, because config can be changed after a
    # run - the report must describe the run that happened. Module 7's
    # budget table reads these.
    provider: str = ""
    model: str = ""
    # Which logs/RUN_HISTORY.md "Run N" this state belongs to. Set once on
    # a fresh run and carried forward by --resume, so continuing a run
    # after a crash/rate-limit appends to the same Run N section instead
    # of opening a new one - see OBSERVATIONS.md, "resume opens a new Run
    # number instead of continuing the last one".
    run_id: int = 0

    # ---- queries -------------------------------------------------------
    @property
    def missing_productions(self) -> list[str]:
        return [p for p in PRODUCTIONS if p not in set(self.reached_productions)]

    @property
    def breadth_fraction(self) -> float:
        return len(set(self.reached_productions)) / len(PRODUCTIONS)

    # ---- updates -------------------------------------------------------
    def observe(self, features: dict, *, accepted: bool) -> bool:
        """Fold one record in. Returns True if its shape was novel.

        Only accepted inputs contribute breadth and depth: a rejected input
        bounced at the front door executed almost no parser code, so counting
        it would inflate the signal while testing nothing.
        """
        from pipeline.features import signature

        sig = signature(features)
        novel = sig not in set(self.seen_signatures)
        if novel:
            self.seen_signatures.append(sig)

        if accepted:
            known = set(self.reached_productions)
            for p in features.get("productions", []):
                if p not in known:
                    self.reached_productions.append(p)
                    known.add(p)
            self.max_depth_reached = max(
                self.max_depth_reached, features.get("max_depth", 0))
        return novel

    # ---- persistence ---------------------------------------------------
    def save(self) -> Path:
        p = _state_path()
        p.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return p

    @classmethod
    def load_or_new(cls) -> "LoopState":
        p = _state_path()
        if not p.exists():
            return cls()
        try:
            return cls(**json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, TypeError):
            return cls()