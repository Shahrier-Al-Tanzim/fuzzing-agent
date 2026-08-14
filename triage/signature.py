"""Parses sanitizer output into a normalized, hashable crash signature.

The signature answers one question: "is this the same bug as that one?"
Two normalization choices dominate, both forced by real crashes we have:

  1. Consecutive identical frames are collapsed. A stack overflow produces
     hundreds of copies of one frame; where the stack happens to run out is
     an accident of stack size, not a property of the bug. Without this, one
     bug reports as dozens.

  2. Harness frames are dropped. Frames in toml_harness.c are our code -
     bucketing on them would split one library bug across the different
     harness paths that reach it.

Both are configurable, and both are recorded in every generated report so
the choices are auditable.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from pipeline.config import load

# "    #4 0x5f9d in parse_array /path/toml.c:1057:30"
FRAME_RE = re.compile(
    r"^\s*#(?P<n>\d+)\s+0x[0-9a-f]+\s+in\s+(?P<func>[\w.:<>~$]+)"
    r"(?:\s+(?P<file>[^\s:]+):(?P<line>\d+))?",
    re.MULTILINE,
)
# Unsymbolized fallback: "    #4 0x5f9d  (/path/bin+0x12a28d)"
FRAME_RAW_RE = re.compile(
    r"^\s*#(?P<n>\d+)\s+0x[0-9a-f]+\s+\((?P<obj>[^)]+)\)", re.MULTILINE)

ASAN_ERROR_RE = re.compile(r"ERROR:\s*AddressSanitizer:\s*([\w-]+)")
UBSAN_ERROR_RE = re.compile(r"([^\s:]+):(\d+):\d+:\s*runtime error:\s*(.+)")
SUMMARY_RE = re.compile(r"SUMMARY:\s*\w*Sanitizer:\s*([\w-]+)")


@dataclass
class CrashSignature:
    bug_type: str                       # e.g. "stack-overflow"
    frames: list[str] = field(default_factory=list)   # normalized, top-N
    signal: int | None = None
    raw_frame_count: int = 0
    collapsed: bool = False             # did recursion collapsing fire?

    @property
    def digest(self) -> str:
        payload = self.bug_type + "|" + "|".join(self.frames)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    @property
    def short(self) -> str:
        top = self.frames[0].split()[0] if self.frames else "unknown"
        return f"{self.bug_type}@{top}"

    def to_dict(self) -> dict:
        return {
            "digest": self.digest,
            "short": self.short,
            "bug_type": self.bug_type,
            "frames": self.frames,
            "signal": self.signal,
            "raw_frame_count": self.raw_frame_count,
            "recursion_collapsed": self.collapsed,
        }


def _normalize_frame(func: str, file: str | None, line: str | None) -> str:
    """Function + file:line, with addresses and absolute paths stripped.

    The line number is kept: two distinct bugs in the same function are
    genuinely different bugs, and dropping it would merge them.
    """
    if file:
        return f"{func} {file.rsplit('/', 1)[-1]}:{line}"
    return func


def _collapse(frames: list[str]) -> tuple[list[str], bool]:
    out: list[str] = []
    collapsed = False
    for f in frames:
        if out and out[-1] == f:
            collapsed = True
            continue
        out.append(f)
    return out, collapsed


def parse_signature(stderr: str, signal: int | None = None) -> CrashSignature | None:
    """Build a signature from sanitizer output. None if it isn't a crash report."""
    cfg = load()
    n_frames = cfg.get("triage.signature_frames", 5)
    do_collapse = cfg.get("triage.collapse_recursive_frames", True)
    ignore = cfg.get("triage.ignore_frame_patterns", [])

    # --- what kind of bug ---
    bug_type = "unknown"
    if m := ASAN_ERROR_RE.search(stderr):
        bug_type = m.group(1)
    elif m := SUMMARY_RE.search(stderr):
        bug_type = m.group(1)
    elif m := UBSAN_ERROR_RE.search(stderr):
        # UBSan: the message text *is* the bug class, and the source location
        # matters more than the stack - include both, trimmed.
        bug_type = f"ubsan:{m.group(3)[:48].strip()}"
    elif signal is not None:
        bug_type = f"signal_{signal}"
    elif "Sanitizer" not in stderr:
        return None

    # --- frames ---
    raw: list[str] = []
    for m in FRAME_RE.finditer(stderr):
        raw.append(_normalize_frame(m.group("func"), m.group("file"), m.group("line")))
    if not raw:
        # Unsymbolized build: fall back to object+offset. Weaker, but stable.
        for m in FRAME_RAW_RE.finditer(stderr):
            obj = m.group("obj")
            raw.append(obj.rsplit("/", 1)[-1])

    raw_count = len(raw)
    frames = [f for f in raw if not any(pat in f for pat in ignore)]

    collapsed = False
    if do_collapse:
        frames, collapsed = _collapse(frames)

    return CrashSignature(
        bug_type=bug_type,
        frames=frames[:n_frames],
        signal=signal,
        raw_frame_count=raw_count,
        collapsed=collapsed,
    )