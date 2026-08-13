"""Versioned on-disk storage for generated strategies.

Saves accepted AND rejected candidates. The rejected ones are the evidence
for the report's "what was harder than expected" section, and they are the
only record of how many attempts a 7B model actually needed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import load


def _dir() -> Path:
    d = load().path("paths.strategies")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _archive_dir() -> Path:
    d = _dir() / "accepted"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _next_archive_number(iteration: int) -> int:
    """1, 2, 3, ... per iteration - so a later run never clobbers an
    earlier pass, independent of how many times you re-ran seed.py."""
    nums = []
    for p in _archive_dir().glob(f"iter_{iteration:02d}_strategy_*.py"):
        tail = p.stem.rsplit("_", 1)[-1]
        if tail.isdigit():
            nums.append(int(tail))
    return max(nums, default=0) + 1


def save_strategy(iteration: int, code: str, *, accepted: bool,
                  attempt: int = 1, meta: dict | None = None) -> Path:
    suffix = "" if accepted else f"_rejected_attempt{attempt}"
    path = _dir() / f"iter_{iteration:02d}_strategy{suffix}.py"
    header = (
        f'"""Generated strategy - iteration {iteration}, attempt {attempt}.\n'
        f"accepted: {accepted}\n"
        f"generated: {datetime.now(timezone.utc).isoformat()}\n"
        f'"""\n'
    )
    path.write_text(header + code, encoding="utf-8")

    if meta is not None:
        meta_path = path.with_suffix(".json")
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # `iter_{N}_strategy.py` stays the single, predictable path Module 5
    # reads for "the current state of iteration N" - it always gets
    # overwritten by the latest pass, on purpose. This archive copy is
    # purely so a later successful test run never erases evidence of an
    # earlier one.
    if accepted:
        n = _next_archive_number(iteration)
        archive_path = _archive_dir() / f"iter_{iteration:02d}_strategy_{n}.py"
        archive_path.write_text(header + code, encoding="utf-8")
        if meta is not None:
            archive_path.with_suffix(".json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8")

    return path


def load_strategy_code(iteration: int) -> str | None:
    path = _dir() / f"iter_{iteration:02d}_strategy.py"
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_strategy_object(iteration: int):
    """Re-exec a saved strategy and return the `toml_strategy` object."""
    code = load_strategy_code(iteration)
    if code is None:
        raise FileNotFoundError(f"no accepted strategy for iteration {iteration}")
    ns: dict = {}
    exec(compile(code, f"<iter_{iteration:02d}_strategy>", "exec"), ns)  # noqa: S102
    return ns["toml_strategy"]


def latest_iteration() -> int | None:
    iters = [
        int(p.name.split("_")[1])
        for p in _dir().glob("iter_*_strategy.py")
        if "rejected" not in p.name
    ]
    return max(iters) if iters else None