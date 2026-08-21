# Crash 3db1e06f41e9 — stack-overflow@strnlen

**Type:** `stack-overflow`
**Occurrences:** 11 input(s) mapped to this signature
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

213121 bytes → 213121 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
k0_L47U = [{ k0 = [{ k1 = [{ k2 = [{ k3 = [{ k4 = [{ k5 = [{ k6 = [{ k7 = [{ k8 = [{ k9 = [{ k10 = [{ k11 = [{ k12 = [{ k13 = [{ k14 = [{ k15 = [{ k16 = [{ k17 = [{ k18 = [{ k19 = [{ k20 = [{ k21 = [{ k22 = [{ k23 = [{ k24 = [{ k25 = [{ k26 = [{ k27 = [{ k28 = [{ k29 = [{ k30 = [{ k31 = [{ k32 = [{ k33 = [{ k34 = [{ k35 = [{ k36 = [{ k37 = [{ k38 = [{ k39 = [{ k40 = [{ k41 = [{ k42 = [{ k43 = [{ k44 = [{ k45 = [{ k46 = [{ k47 = [{ k48 = [{ k49 = [{ k50 = [{ k51 = [{ k52 = [{ k53 = [{ k54 = [{ k55 = [{ k56 = [{ k57 = [{ k58 = [{ k59 = [{ k60 = [{ k61 = [{ k62 = [{ k63 = [{ k64 = [{ k65 = [{ k66 = [{ k67 = [{ k68 = [{ k69 = [{ k70 = [{ k71 = [{ k72 = [{ k73 = [{ k74 = [{ k75 = [{ k76 = [{ k77 = [{ k78 = [{ k79 = [{ k80 = [{ k81 = [{ k82 = [{ k83 = [{ k84 = [{ k85 = [{ k86 = [{ k87 = [{ k88 = [{ k89 = [{ k90 = [{ k91 = [{ k92 = [{ k93 = [{ k94 = [{ k95 = [{ k96 = [{ k97 = [{ k98 = [{ k99 = [{ k100 = [{ k101 = [{ k102 = [{ k103 = [{ k104 = [{ k105 = [{ k106 = [{ k107 = [{ k108 = [{ k109 = [{ k110 = [{ k111 = [{ k112 = [{ k113 = [{ k114 = [{ k115 = [{ k116 = [{ k117 = [{ k118 = [{ k119 = [{ k120 = [{ k121 = [{ k122 = [{ k123 = [{ k124 = [{ k125 = [{ k126 = [{ k127 = [{ k128 = [{ k129 = [{ k130 = [{ k131 = [{ k132 = [{ k133 = [{ k134 = [{ k135 = [{ k136 = [{ k137 = [{ k138 = [{ k139 = [{ k140 = [{ k141 = [{ k142 = [{ k143 = [{ k144 = [{ k145 = [{ k146 = [{ k147 = [{ k148 = [{ k149 = [{ k150 = [{ k151 = [{ k152 = [{ k153 = [{ k154 = [{ k155 = [{ k156 = [{ k157 = [{ k158 = [{ k159 = 
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_29/alternating_array_inline_table_nesting-3db1e06f41e9/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
