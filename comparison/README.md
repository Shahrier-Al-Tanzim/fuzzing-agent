# Provider comparison — Groq vs Gemini vs Claude

This folder groups the fuzzing loop's runs **by the LLM provider that drove
them**, so the three can be compared side by side. Nothing here is a source
of truth — every file is a **copy** of an artifact that already lives in its
normal place (`agent/strategies/accepted/`, `triage/reports/`,
`logs/RUN_HISTORY.jsonl`). The originals are untouched.

## Which runs used which provider

| Provider | Runs | Model | Per-run code archived? | Per-run triage archived? |
|---|---|---|---|---|
| **Groq** | 1–12 | `llama-3.3-70b-versatile` | ❌ no (see `groq/README.md`) | ❌ no |
| **Gemini** | 15–21 | `gemini-3.6-flash` | ✅ runs 17, 19, 20, 21 | ✅ runs 17, 20, 21 |
| **Claude** | — | *(to be run)* | — | — |

Runs **13, 14, 18** were stopped before completing (an error or Ctrl+C, not a
generation result) and carry no provider tag, so they are excluded from the
provider folders. They still appear in `logs/RUN_HISTORY.md` for the record.

## What each folder contains

```
comparison/
  groq/      metrics.md + metrics.csv (runs 1–12) + README on the archival gap
  gemini/    metrics.md + metrics.csv (runs 15–21)
             run_17/  run_19/  run_20/  run_21/   each with:
               strategies/   the accepted .py + .json per iteration
               triage/       the crash reports (INDEX.md + per-signature dirs)
  claude/    README placeholder — ready to receive runs once Claude is added
```

## The one asymmetry to keep in mind for the analysis

The per-run folder scheme (`run_NN/`) was only introduced during the Gemini
era. So **Gemini has full per-run code + triage; Groq has metrics only.** The
Groq strategy code and crash reports were never archived into run folders and
cannot be cleanly reconstructed (the old `iter_XX_strategy_N.py` files use a
global success counter with no provider or run_id tag). See `groq/README.md`.

For an apples-to-apples comparison, the **`metrics.md` / `metrics.csv` files
are the common denominator** — they exist for every completed run of both
providers, extracted identically from `logs/RUN_HISTORY.jsonl` (acceptance,
coverage, novelty, max depth, findings, examples, elapsed time per iteration,
plus tokens and attempt counts per run). Claude runs will produce the same
files, so the three become directly comparable on those axes.

## How this was generated

Regenerate after new runs by re-running the assembly step (copies + metrics
extraction from `logs/RUN_HISTORY.jsonl`). Metrics come straight from the run
log; the Gemini `run_NN/` folders are `cp` copies of
`agent/strategies/accepted/run_NN/` and `triage/reports/run_NN/`.
