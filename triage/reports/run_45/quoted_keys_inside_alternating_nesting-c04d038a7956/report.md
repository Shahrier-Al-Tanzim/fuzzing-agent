# Crash c04d038a7956 — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 98 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (2/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  expand toml.c:411
  #2  norm_basic_str toml.c:506
  #3  normalize_key toml.c:652
  #4  create_keyarray_in_table toml.c:830
```

Raw frames before normalization: 188
Consecutive identical frames collapsed: False

## Minimized reproducer

160008 bytes → 152008 bytes (5% smaller) via `delta-debugging` in 4 steps.

```toml
deep = [{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"=[{"k"
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_45/quoted_keys_inside_alternating_nesting-c04d038a7956/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
