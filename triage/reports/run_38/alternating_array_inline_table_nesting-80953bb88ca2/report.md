# Crash 80953bb88ca2 — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 133 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (1/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  expand toml.c:411
  #2  expand_arritem toml.c:436
  #3  create_table_in_array toml.c:903
  #4  parse_array toml.c:1072
```

Raw frames before normalization: 188
Consecutive identical frames collapsed: False

## Minimized reproducer

160005 bytes → 160005 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
k = [{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_38/alternating_array_inline_table_nesting-80953bb88ca2/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
