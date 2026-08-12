# Module 3 — Baseline Pipeline

End-to-end plumbing: generate → serialize → run harness → classify → log.
Deliberately grammar-unaware. The point is correctness, not bug-finding.

## Contents
- `config.py`  — loads config.yaml, the single source of tunables
- `schema.py`  — `RunRecord` / `Verdict`; the JSONL contract Modules 5–7 read
- `runner.py`  — `HarnessRunner.run(text)` → `RunRecord`; `RunLogger` (JSONL)
- `baseline_strategy.py` — three naive tiers, increasing plausibility
- `run_baseline.py`      — driver + pipeline health check

## Key design decisions
- **JSONL, flushed per line**: a run killed mid-way still leaves a valid log.
- **Sanitizer output beats exit code.** A sanitizer report is authoritative
  however the process died; reading the exit code first would file a real
  memory-safety bug as a clean rejection.
- **Unknown exit codes are crashes.** A false finding gets discarded in
  triage; a dropped real one is gone.
- **TIMEOUT is stored distinctly from CRASH** even though the assignment
  counts it as a crash — collapsing later is trivial, splitting later is
  impossible.
- **No assert in the baseline.** Asserting would trigger Hypothesis's
  shrinker on first crash and truncate the census. Shrinking is Module 6.
- **Three baseline tiers.** Without a tier that actually gets accepted, a 0%
  acceptance rate can't distinguish a bad generator from a broken runner.

## Run
    python -m pipeline.run_baseline
    python -m pipeline.run_baseline --strategy keyvalue_lines --max-examples 50