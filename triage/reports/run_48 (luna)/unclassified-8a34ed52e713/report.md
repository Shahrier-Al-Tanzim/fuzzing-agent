# Crash 8a34ed52e713 — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 1 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (0/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  CALLOC toml.c:58
  #2  create_array_in_array toml.c:887
  #3  parse_array toml.c:1057
  #4  parse_array toml.c:1060
```

Raw frames before normalization: 179
Consecutive identical frames collapsed: True

## Minimized reproducer

163570 bytes → 160174 bytes (2% smaller) via `delta-debugging` in 400 steps.

```toml
deep_quoted_array = [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ [ [
[ 
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_48/unclassified-8a34ed52e713/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
