# Crash 26e809dd9d85 — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 80 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (1/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  STRNDUP toml.c:85
  #2  normalize_key toml.c:681
  #3  create_keytable_in_table toml.c:782
  #4  parse_keyval toml.c:1177
```

Raw frames before normalization: 181
Consecutive identical frames collapsed: False

## Minimized reproducer

320008 bytes → 320008 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
deep = {a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a={a
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_45/nested_inline_tables-26e809dd9d85/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
