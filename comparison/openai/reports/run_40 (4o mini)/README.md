# OpenAI (placeholder — ready for runs)

This folder is ready to receive OpenAI runs once the OpenAI provider is selected and executed in the loop.

When those runs complete, populate it to match the **Gemini** layout so the providers stay directly comparable:

```
openai/
  metrics.md      per-run, per-iteration metrics (from logs/RUN_HISTORY.jsonl)
  metrics.csv     the same numbers, flat, for spreadsheets/pandas
  run_NN/
    strategies/   copy of agent/strategies/accepted/run_NN/
    triage/       copy of triage/reports/run_NN/
```

## Setup & Execution

1. `OPENAI_API_KEY` is loaded from `.env`.
2. Model client handles OpenAI's `/v1/chat/completions` API endpoint (matching the structure of `gemini_client.py`).
3. Results will produce per-run strategies, triage reports, and metrics logs for side-by-side comparison against Gemini and Groq.
