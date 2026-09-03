# Crash unparsed_timeout — unparsed

**Type:** `unknown`
**Occurrences:** 202 input(s) mapped to this signature
**Verification:** deterministic (3/3 runs crashed)

## Normalized stack (top 0 frames)

```
  (none parsed)
```

Raw frames before normalization: 0
Consecutive identical frames collapsed: False

## Minimized reproducer

420889 bytes → 420889 bytes (0% smaller) via `none` in 0 steps.

```toml
"key 0" = 0
key_1 = 0
key_2 = 0
key_3 = 0
key_4 = 0
"key 5" = 0
key_6 = 0
key_7 = 0
key_8 = 0
key_9 = 0
"key 10" = 0
key_11 = 0
key_12 = 0
key_13 = 0
key_14 = 0
"key 15" = 0
key_16 = 0
key_17 = 0
key_18 = 0
key_19 = 0
"key 20" = 0
key_21 = 0
key_22 = 0
key_23 = 0
key_24 = 0
"key 25" = 0
key_26 = 0
key_27 = 0
key_28 = 0
key_29 = 0
"key 30" = 0
key_31 = 0
key_32 = 0
key_33 = 0
key_34 = 0
"key 35" = 0
key_36 = 0
key_37 = 0
key_38 = 0
key_39 = 0
"key 40" = 0
key_41 = 0
key_42 = 0
key_43 = 0
key_44 = 0
"key 45" = 0
key_46 = 0
key_47 = 0
key_48 = 0
key_49 = 0
"key 50" = 0
key_51 = 0
key_52 = 0
key_53 = 0
key_54 = 0
"key 55" = 0
key_56 = 0
key_57 = 0
key_58 = 0
key_59 = 0
"key 60" = 0
key_61 = 0
key_62 = 0
key_63 = 0
key_64 = 0
"key 65" = 0
key_66 = 0
key_67 = 0
key_68 = 0
key_69 = 0
"key 70" = 0
key_71 = 0
key_72 = 0
key_73 = 0
key_74 = 0
"key 75" = 0
key_76 = 0
key_77 = 0
key_78 = 0
key_79 = 0
"key 80" = 0
key_81 = 0
key_82 = 0
key_83 = 0
key_84 = 0
"key 85" = 0
key_86 = 0
key_87 = 0
key_88 = 0
key_89 = 0
"key 90" = 0
key_91 = 0
key_92 = 0
key_93 = 0
key_94 = 0
"key 95" = 0
key_96 = 0
key_97 = 0
key_98 = 0
key_99 = 0
"key 100" = 0
key_101 = 0
key_102 = 0
key_103 = 0
key_104 = 0
"key 105" = 0
key_106 = 0
key_107 = 0
key_108 = 0
key_109 = 0
"key 110" = 0
key_111 = 0
key_112 = 0
key_113 = 0
key_114 = 0
"key 115" = 0
key_116 = 0
key_117 = 0
key_118 = 0
key_119 = 0
"key 120" = 0
key_121 = 0
key_122 = 0
key_123 = 0
key_124 = 0
"key 125" = 0
key_126 = 0
key_127 = 0
key_128 = 0
key_129 = 
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_50/many_sibling_keys_a_hang_not_a_crash-unparsed_timeout/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
