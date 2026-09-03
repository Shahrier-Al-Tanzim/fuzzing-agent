# Crash unparsed_timeout — unparsed

**Type:** `unknown`
**Occurrences:** 201 input(s) mapped to this signature
**Verification:** DID NOT REPRODUCE (0/3)

## Normalized stack (top 0 frames)

```
  (none parsed)
```

Raw frames before normalization: 0
Consecutive identical frames collapsed: False

## Minimized reproducer

164905 bytes → 164905 bytes (0% smaller) via `none` in 0 steps.

```toml
[many_siblings]
k0 = true
k1 = false
k2 = false
k3 = true
k4 = false
k5 = false
k6 = true
k7 = false
k8 = false
k9 = true
k10 = false
k11 = false
k12 = true
k13 = false
k14 = false
k15 = true
k16 = false
k17 = false
k18 = true
k19 = false
k20 = false
k21 = true
k22 = false
k23 = false
k24 = true
k25 = false
k26 = false
k27 = true
k28 = false
k29 = false
k30 = true
k31 = false
k32 = false
k33 = true
k34 = false
k35 = false
k36 = true
k37 = false
k38 = false
k39 = true
k40 = false
k41 = false
k42 = true
k43 = false
k44 = false
k45 = true
k46 = false
k47 = false
k48 = true
k49 = false
k50 = false
k51 = true
k52 = false
k53 = false
k54 = true
k55 = false
k56 = false
k57 = true
k58 = false
k59 = false
k60 = true
k61 = false
k62 = false
k63 = true
k64 = false
k65 = false
k66 = true
k67 = false
k68 = false
k69 = true
k70 = false
k71 = false
k72 = true
k73 = false
k74 = false
k75 = true
k76 = false
k77 = false
k78 = true
k79 = false
k80 = false
k81 = true
k82 = false
k83 = false
k84 = true
k85 = false
k86 = false
k87 = true
k88 = false
k89 = false
k90 = true
k91 = false
k92 = false
k93 = true
k94 = false
k95 = false
k96 = true
k97 = false
k98 = false
k99 = true
k100 = false
k101 = false
k102 = true
k103 = false
k104 = false
k105 = true
k106 = false
k107 = false
k108 = true
k109 = false
k110 = false
k111 = true
k112 = false
k113 = false
k114 = true
k115 = false
k116 = false
k117 = true
k118 = false
k119 = false
k120 = true
k121 = false
k122 = false
k123 = true
k124 = false
k125 = fals
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_51/many_sibling_keys_a_hang_not_a_crash-unparsed_timeout/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
