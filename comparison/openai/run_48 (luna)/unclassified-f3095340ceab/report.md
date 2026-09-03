# Crash f3095340ceab — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 6 input(s) mapped to this signature
**Verification:** deterministic (3/3 runs crashed)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  expand toml.c:411
  #2  norm_basic_str toml.c:506
  #3  normalize_key toml.c:652
  #4  create_keytable_in_table toml.c:782
```

Raw frames before normalization: 190
Consecutive identical frames collapsed: True

## Minimized reproducer

777110 bytes → 777110 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".c."quoted key".b."quoted key".a."quoted key".b."quoted key".b."quoted key".c."quoted key".b."quoted key".b."quoted key".a."quoted key".b."quoted key".c."quoted key".a."quoted key".b."quoted key".b."quoted key".a."quoted key".
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_48/unclassified-f3095340ceab/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
