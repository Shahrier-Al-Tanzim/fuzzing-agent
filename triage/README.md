# Module 6 — Crash Triage

Raw crashes → deduplicated, minimized, verified bug reports.

## Contents
- `signature.py`  — parse sanitizer output → normalized, hashable signature
- `minimize.py`   — Path A: Hypothesis shrinking; Path B: delta debugging
- `verify.py`     — re-run a reproducer N times; deterministic vs flaky
- `run_triage.py` — driver: collect → dedupe → minimize → verify → report

## Deduplication normalization (graded — documented deliberately)
1. **Consecutive identical frames collapsed.** A stack overflow emits
   hundreds of copies of one frame; where the stack runs out is an accident
   of stack size, not a property of the bug. Without collapsing, one bug
   reports as dozens.
2. **Harness frames dropped.** Frames in `toml_harness.c`, the sanitizer
   runtime, and libc startup are excluded, so signatures describe the
   library's bug and not our path into it.
3. **Frame identity is `function file:line`.** Addresses and absolute paths
   are stripped; the line number is kept, because two bugs in one function
   are two bugs.
4. **Top 5 frames** are hashed (`triage.signature_frames`).

## Minimization: two paths, and why
Hypothesis shrinks the *choice sequence* behind a generated value, so it can
only shrink values it produced. Crashing inputs recovered from a JSONL log
have no generating strategy attached, so:
- `shrink_with_hypothesis()` — used when the strategy is in hand (preferred)
- `minimize_concrete()` — delta debugging for inputs from logs/by hand

Every candidate must reproduce **the same signature**, not merely crash, so
minimization cannot silently drift onto a different bug.

## Run
    python -m triage.run_triage
    python -m triage.run_triage --no-minimize
    python -m triage.run_triage --extra path/to/other_crash.toml