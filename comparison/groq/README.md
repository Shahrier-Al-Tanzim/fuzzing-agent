# Groq (runs 1–12, `llama-3.3-70b-versatile`)

## What's here

- **`metrics.md`** — per-run, per-iteration metrics (acceptance, coverage,
  novelty, max depth, findings, examples, elapsed time) plus a run-level
  summary (model, status, attempts, total tokens), for all 12 Groq runs.
- **`metrics.csv`** — the same numbers, flat, one row per iteration, for
  loading into a spreadsheet or pandas.

Both are extracted directly from `logs/RUN_HISTORY.jsonl`.

## What's NOT here, and why

**No per-run strategy code, and no per-run triage reports.** This is a real
gap, documented honestly rather than papered over:

- The per-run archive scheme (`agent/strategies/accepted/run_NN/` and
  `triage/reports/run_NN/`) did not exist yet when the Groq runs happened. It
  was introduced during the Gemini era.
- The Groq-era strategy files that *were* saved use the old scheme
  `agent/strategies/accepted/iter_XX_strategy_N.py`, where `N` is a **global
  success counter** across all runs — with **no `provider` and no `run_id`
  field** in the accompanying `.json`. So they cannot be mapped back to a
  specific Groq run number.
- No triage was ever run on the Groq runs' outputs, so no crash reports exist
  for them at all.

The strategy code could, in principle, be dug out of git history commit by
commit, but commits do not map 1:1 to runs, so any attribution would be
approximate. That reconstruction was deliberately **not** done — the metrics
are the reliable, run-attributable record for Groq.

## Using Groq for the comparison

Compare Groq against Gemini (and later Claude) on the **metrics** axes only:
acceptance rate, coverage, novelty, max nesting depth reached, findings
count, and cost/speed (tokens, attempts, elapsed time). These are complete
and directly comparable across all three providers. Deeper artifact-level
comparison (actual generated code, actual crash signatures) is only possible
for Gemini and Claude, which have full per-run folders.
