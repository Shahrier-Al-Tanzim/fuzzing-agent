# Crash e1e7b894bf33 — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 14 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (1/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  STRNDUP toml.c:85
  #2  normalize_key toml.c:646
  #3  create_keytable_in_table toml.c:782
  #4  parse_keyval toml.c:1177
```

Raw frames before normalization: 184
Consecutive identical frames collapsed: False

## Minimized reproducer

480544 bytes → 456517 bytes (5% smaller) via `delta-debugging` in 4 steps.

```toml
deep = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { 'q' = { k = { '
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_50/unclassified-e1e7b894bf33/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
