# Final testing — the report's provider comparison

This is the destination for the **final, controlled comparison batch** used
in the report: fresh runs under identical current settings (same prompt
rules, same 5-iteration budget), one folder per provider. Kept separate from
`comparison/gemini/` and `comparison/claude/` (the earlier, mixed-condition
historical runs / placeholder) so the report's headline numbers come from a
clean, apples-to-apples batch rather than runs collected at different points
in the project as prompt rules changed.

## Plan

| Provider | Planned runs | Status | Run #s (auto-assigned by `agent/loop.py`) |
|---|---|---|---|
| Gemini (`gemini-3.6-flash`) | 5 | Running 2026-09-02 | 35–39 (Run 34 excluded — see below) |
| Claude (Opus 5, `claude-opus-5`) | 5 | Planned 2026-09-03, pending `agent/claude_client.py` | 40–44 (expected) |
| Groq (`llama-3.3-70b-versatile`) | — | Not re-run | Reusing existing archived runs 1–12 in `comparison/groq/` — see that folder's README for why (the model was deprecated and current Groq free-tier models can't clear this project's prompt size without constant rate-limiting) |

Run numbers above are *expected*, not guaranteed — `agent/loop.py` assigns
the next number automatically each time a run starts, so if anything else
runs in between, actual numbers may shift. Check `logs/RUN_HISTORY.md` for
the real numbers once runs are done.

**Run 34 is excluded from the clean batch.** It completed fine (see
`logs/RUN_HISTORY.md`, aggregate metrics only: findings 291/237/173/138/128
across its 5 iterations), but triage was never run on it before Run 35
started, and `pipeline/logs/iteration_NN.jsonl` are shared filenames that
get overwritten by the next run — so Run 34's raw crash data (reproducer
bytes, sanitizer stack traces) is gone. It can still be cited as a metrics
data point, just not as a source of deduplicated/verified crash reports.
**Lesson applied going forward: run `triage.run_triage` immediately after
each run finishes, before starting the next one**, for every run in 35–39
and 40–44.

## Layout

Each provider folder should end up matching the layout already established
in `comparison/gemini/` and `comparison/claude/`:

```
final_testing/
  gemini/
    metrics.md / metrics.csv       per-run, per-iteration metrics
    run_34/ .. run_38/             strategies/ + triage/ copies
  claude/
    metrics.md / metrics.csv
    run_39/ .. run_43/
```

Nothing here is a source of truth — everything is a **copy** of what
`agent/loop.py`/`triage` already write to `agent/strategies/accepted/run_NN/`
and `triage/reports/run_NN/`. Populate after each batch finishes by copying
those folders + extracting metrics from `logs/RUN_HISTORY.jsonl`, same
process used for `comparison/gemini/`.

## Status log

- 2026-09-02: folder created, empty. Gemini batch (5 runs) starting today.
