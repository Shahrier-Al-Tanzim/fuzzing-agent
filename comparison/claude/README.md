# Claude (placeholder — no runs yet)

This folder is ready to receive Claude runs once a Claude provider is added
to the loop. When those runs happen, populate it to match the **Gemini**
layout so the three providers stay directly comparable:

```
claude/
  metrics.md      per-run, per-iteration metrics (from logs/RUN_HISTORY.jsonl)
  metrics.csv     the same numbers, flat, for spreadsheets/pandas
  run_NN/
    strategies/   copy of agent/strategies/accepted/run_NN/
    triage/       copy of triage/reports/run_NN/
```

## To add Claude to the loop

At the config/provider level this mirrors how Groq and Gemini were added
(`config.yaml`'s `llm` block plus a client module like `agent/gemini_client.py`).
Pick the current best Claude model at that time rather than hardcoding an old
id — check the live model list before running. Once runs exist, regenerate
this folder the same way the others were built (copy the `run_NN/` artifacts,
extract metrics from the run log).

## What to compare

The common denominator across all three providers is the **metrics** set:
acceptance, coverage, novelty, max depth, findings, examples, elapsed time,
tokens, and attempts. Claude will additionally have full per-run code and
triage (like Gemini), enabling artifact-level comparison where Groq can only
offer metrics.
