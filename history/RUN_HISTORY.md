# Run History

**Auto-generated from `RUN_HISTORY.jsonl` — do not edit by hand,** this file is fully rewritten every time a new attempt is logged.
Every generation attempt, across every run of `agent.seed` and `agent.loop`, grouped by iteration, oldest attempt first within each group.

**Total: 15/26 attempts passed, across 5 distinct iteration numbers.**

## Iteration 0 — 7/17 attempts passed

| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |
|---|---|---|---|---|---|---|---|---|
| 2026-08-13 07:25:56 | backfill | 1 | FAIL | draw | groq/llama-3.3-70b-versatile | 4862 | 1.92 | drawing an example raised TypeError: dates() got an unexpected keyword argument 'min_date'… |
| 2026-08-13 07:25:56 | backfill | 2 | FAIL | draw | groq/llama-3.3-70b-versatile | 5137 | 2.33 | produced non-str values (['list']). Every example must be a `str` of TOML text - add .map(… |
| 2026-08-13 07:25:56 | backfill | 3 | PASS | acceptance | groq/llama-3.3-70b-versatile | 4900 | 12.83 |  |
| 2026-08-13 08:28:01 | backfill | 1 | FAIL | draw | groq/llama-3.3-70b-versatile | 4946 | 1.86 | drawing an example raised TypeError: dates() got an unexpected keyword argument 'min_date'… |
| 2026-08-13 08:28:01 | backfill | 2 | FAIL | acceptance | groq/llama-3.3-70b-versatile | 4926 | 1.61 | only 0/40 (0%) of generated documents were accepted by tomlc99; the floor is 20%. The most… |
| 2026-08-13 08:28:01 | backfill | 3 | PASS | acceptance | groq/llama-3.3-70b-versatile | 4990 | 13.86 |  |
| 2026-08-13 08:31:38 | backfill | 1 | FAIL | draw | groq/llama-3.3-70b-versatile | 4917 | 1.87 | drawing an example raised InvalidArgument: Expected date but got min_value='1970-01-01' (t… |
| 2026-08-13 08:31:38 | backfill | 2 | PASS | acceptance | groq/llama-3.3-70b-versatile | 4816 | 1.39 |  |
| 2026-08-13 08:41:33 | backfill | 1 | FAIL | draw | groq/llama-3.3-70b-versatile | 5109 | 2.41 | drawing an example raised AttributeError: 'str' object has no attribute 'map' |
| 2026-08-13 08:41:33 | backfill | 2 | FAIL | acceptance | groq/llama-3.3-70b-versatile | 4805 | 1.35 | only 2/40 (5%) of generated documents were accepted by tomlc99; the floor is 20%. The most… |
| 2026-08-13 08:41:33 | backfill | 3 | PASS | acceptance | groq/llama-3.3-70b-versatile | 4952 | 13.85 |  |
|  | backfill | 1 | FAIL | draw | unknown/unknown | 5244 | 2.55 | drawing an example raised AttributeError: 'list' object has no attribute 'map' |
|  | backfill | 2 | PASS | acceptance | unknown/unknown | 5084 | 2.16 |  |
|  | backfill | 1 | FAIL | draw | unknown/unknown | 4821 | 1.7 | drawing an example raised InvalidArgument: Cannot have allow_nan=True, with min_value or m… |
|  | backfill | 2 | FAIL | draw | unknown/unknown | 4933 | 1.96 | drawing an example raised AttributeError: 'tuple' object has no attribute 'map' |
|  | backfill | 3 | PASS | acceptance | unknown/unknown | 4911 | 10.75 |  |
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 6333 | 2.64 |  |

## Iteration 1 — 2/2 attempts passed

| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |
|---|---|---|---|---|---|---|---|---|
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 5592 | 1.94 |  |
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 7511 | 2.96 |  |

## Iteration 2 — 2/2 attempts passed

| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |
|---|---|---|---|---|---|---|---|---|
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 5863 | 1.82 |  |
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 7835 | 14.33 |  |

## Iteration 3 — 2/2 attempts passed

| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |
|---|---|---|---|---|---|---|---|---|
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 6080 | 1.99 |  |
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 7838 | 2.62 |  |

## Iteration 4 — 2/3 attempts passed

| At (UTC) | Source | Attempt | Result | Stage | Provider / Model | Tokens | Sec | Error |
|---|---|---|---|---|---|---|---|---|
|  | backfill | 1 | FAIL | draw | unknown/unknown | 6294 | 2.76 | produced non-str values (['list']). Every example must be a `str` of TOML text - add .map(… |
|  | backfill | 2 | PASS | acceptance | unknown/unknown | 6229 | 2.35 |  |
|  | backfill | 1 | PASS | acceptance | unknown/unknown | 7876 | 2.78 |  |
