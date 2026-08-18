"""Runs one input through the sanitizer-built harness and classifies it.

Classification order matters and is deliberate:

  1. Timeout        - the process never returned, nothing else to read.
  2. Sanitizer text - checked BEFORE the exit code, because a sanitizer
                      report is authoritative regardless of how the process
                      finally died.
  3. Fatal signal   - negative returncode on POSIX.
  4. Exit code      - the harness's own contract.

Getting 2 and 4 the wrong way round is the classic bug here: a sanitizer
can fire after the harness has already decided to return 2, and reading the
code first would file a real memory-safety bug as a clean rejection.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from pipeline.config import load, PROJECT_ROOT
from pipeline.schema import RunRecord, Verdict

# Sanitizer banners. Kept broad on purpose - a missed sanitizer report is a
# missed bug, while a false positive is caught immediately during triage.
SANITIZER_PATTERNS = re.compile(
    r"AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|"
    r"runtime error:|SUMMARY: \w*Sanitizer",
    re.IGNORECASE,
)

# ASan: "ERROR: AddressSanitizer: heap-buffer-overflow on address ..."
ASAN_TYPE = re.compile(r"AddressSanitizer:\s*([a-z0-9-]+)")
# UBSan: "file.c:12:34: runtime error: signed integer overflow: ..."
UBSAN_TYPE = re.compile(r"runtime error:\s*([^\n]{0,80})")

REJECT_LINE = re.compile(r"^REJECT:\s*(.*)$", re.MULTILINE)

STDERR_LIMIT = 20000  # keep logs readable; a real crash we've observed (deep
# array-nesting stack overflow) produces a 34,000+ char ASan report - 8000
# was cutting that down to just the top frames. 20000 keeps far more of the
# real report while still bounding log size.


class HarnessRunner:
    def __init__(self, iteration: int = 0) -> None:
        cfg = load()
        self.binary = cfg.path("harness.binary")
        self.timeout = cfg.get("harness.timeout_seconds", 5)
        self.iteration = iteration

        self.exit_accept = cfg.get("harness.exit_accept", 0)
        self.exit_reject = cfg.get("harness.exit_reject", 2)
        self.exit_usage = cfg.get("harness.exit_usage", 64)
        self.exit_sanitizer = cfg.get("harness.exit_sanitizer", 86)

        if not self.binary.exists():
            raise FileNotFoundError(
                f"harness not built: {self.binary}\nrun ./harness/build.sh"
            )

        self.env = dict(os.environ)
        self.env.update(_sanitizer_env())

    def run(self, text: str, example_index: int = 0) -> RunRecord:
        digest = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
        raw = text.encode("utf-8", "surrogatepass")

        # A real file rather than stdin: it reproduces exactly what a user
        # would do, and a saved crashing input is then byte-identical to
        # what the harness actually consumed.
        with tempfile.NamedTemporaryFile(
            suffix=".toml", delete=False, dir=_scratch_dir()
        ) as tf:
            tf.write(raw)
            tmp_path = tf.name

        started = time.perf_counter()
        timed_out = False
        proc = None
        try:
            proc = subprocess.run(
                [str(self.binary), tmp_path],
                capture_output=True,
                timeout=self.timeout,
                env=self.env,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stderr_bytes = exc.stderr or b""
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if not timed_out:
            stderr_bytes = proc.stderr or b""
        stderr = stderr_bytes.decode("utf-8", "replace")

        record = RunRecord(
            run_id=digest[:16],
            iteration=self.iteration,
            example_index=example_index,
            input_text=text,
            input_bytes=len(raw),
            input_sha256=digest,
            verdict=Verdict.CRASH.value,   # overwritten below
            exit_code=None,
            signal=None,
            duration_ms=round(duration_ms, 2),
            stderr=stderr[:STDERR_LIMIT],
        )

        # --- 1. timeout ---
        if timed_out:
            record.verdict = Verdict.TIMEOUT.value
            return record

        returncode = proc.returncode

        # --- 2. sanitizer output (authoritative, checked before exit code) ---
        if SANITIZER_PATTERNS.search(stderr):
            record.verdict = Verdict.CRASH.value
            record.exit_code = returncode
            m = ASAN_TYPE.search(stderr) or UBSAN_TYPE.search(stderr)
            record.sanitizer_type = m.group(1).strip() if m else "unknown"
            return record

        # --- 3. fatal signal ---
        if returncode < 0:
            record.verdict = Verdict.CRASH.value
            record.signal = -returncode
            record.sanitizer_type = f"signal_{-returncode}"
            return record

        record.exit_code = returncode

        # --- 4. the harness's own contract ---
        if returncode == self.exit_accept:
            record.verdict = Verdict.ACCEPT.value
        elif returncode == self.exit_reject:
            record.verdict = Verdict.REJECT.value
            m = REJECT_LINE.search(stderr)
            record.reject_message = m.group(1).strip() if m else stderr.strip()[:200]
        elif returncode == self.exit_usage:
            # Our bug, or an input the harness refused as oversized. Never a
            # library finding.
            record.verdict = Verdict.HARNESS_ERROR.value
        elif returncode == self.exit_sanitizer:
            # Sanitizer exit code without a recognizable banner - unusual,
            # but trust the code.
            record.verdict = Verdict.CRASH.value
            record.sanitizer_type = "sanitizer_exitcode_no_banner"
        else:
            # Unknown code. Treat as a crash: better a false finding that
            # triage discards than a real one silently dropped.
            record.verdict = Verdict.CRASH.value
            record.sanitizer_type = f"unexpected_exit_{returncode}"

        return record


# A deep-recursion stack overflow is inherently unstable in whether ASan can
# unwind its backtrace (see info.md "unstable signature"). When it can't, the
# report has zero frames, and every frameless overflow then hashes to the same
# "unparsed" signature - collapsing genuinely distinct bugs (deep-array vs
# deep-dotted-key vs deep-inline-table, which have different top frames) into
# one bucket. Retrying a crash a few times to obtain a parseable stack fixes
# that: the crash is still the crash, we just want frames so distinct bugs
# bucket correctly. Used by both triage collection (for --extra inputs) and the
# crash-hunt driver (so logged crashes carry parseable frames, since triage
# reads stored stderr from logs without re-running them).
PARSEABLE_CRASH_RETRIES = 6


def run_for_parseable_crash(runner: "HarnessRunner", text: str,
                            retries: int = PARSEABLE_CRASH_RETRIES) -> "RunRecord":
    """Run `text` until it crashes with a parseable stack, or retries run out.

    Returns the first record whose crash produced parseable frames; else the
    last crashing record (so a genuinely always-frameless crash is still
    reported, just in the unparsed bucket); else the last record (no crash).
    """
    from triage.signature import parse_signature  # local: avoid import cycle

    last = None
    last_crash = None
    for _ in range(max(1, retries)):
        rec = runner.run(text)
        last = rec
        if rec.is_finding:
            last_crash = rec
            sig = parse_signature(rec.stderr, rec.signal)
            if sig is not None and sig.frames:
                return rec
    return last_crash or last


class RunLogger:
    """Appends RunRecords to a JSONL file, flushing each line.

    Flushing per line costs throughput but means a run killed by Ctrl-C or
    the wall-clock cap still leaves a complete, readable log.
    """

    def __init__(self, name: str) -> None:
        log_dir = load().path("paths.logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.path: Path = log_dir / f"{name}.jsonl"
        self._fh = open(self.path, "a", encoding="utf-8")

    def write(self, record: RunRecord) -> None:
        self._fh.write(record.to_json() + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "RunLogger":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _sanitizer_env() -> dict[str, str]:
    """Parse harness/sanitizer_env.sh so Python and bash can never disagree."""
    env: dict[str, str] = {}
    script = PROJECT_ROOT / "harness" / "sanitizer_env.sh"
    if not script.exists():
        return env
    for line in script.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        key, _, value = line[len("export "):].partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _scratch_dir() -> str:
    d = PROJECT_ROOT / "pipeline" / ".scratch"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)