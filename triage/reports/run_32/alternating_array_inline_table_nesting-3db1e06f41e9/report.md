# Crash 3db1e06f41e9 — stack-overflow@strnlen

**Type:** `stack-overflow`
**Occurrences:** 38 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (1/3 matched)

## Normalized stack (top 5 frames)

```
  #0  strnlen
  #1  STRNDUP toml.c:84
  #2  normalize_key toml.c:681
  #3  create_keyarray_in_table toml.c:830
  #4  parse_keyval toml.c:1168
```

Raw frames before normalization: 188
Consecutive identical frames collapsed: False

## Minimized reproducer

360012 bytes → 360012 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
deep_key = [{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[{a=[
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_32/alternating_array_inline_table_nesting-3db1e06f41e9/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
