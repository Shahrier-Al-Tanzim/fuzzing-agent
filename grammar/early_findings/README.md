# Early findings

Bugs found by hand during Module 1 grammar probing, before the fuzzing
pipeline existed. Kept separate from `sample_inputs/` because these are
crash reproducers, not accept/reject probes — running them through
`probe.sh` on a machine without the exact same stack ulimit may or may not
reproduce, and a SIGSEGV in the middle of the probe loop is not what that
script is for.

## 01_array_nesting_stackoverflow.toml

**Symptom:** `toml_json` (built from `harness/vendor/tomlc99` @ pinned
commit `5221b3d3`, no sanitizers, default `ulimit -s` = 8192 KB) segfaults
(signal 11) on deeply nested arrays.

**Repro:**
```bash
python3 -c "
depth = 60000
print('x = ' + '[' * depth + '1' + ']' * depth)
" | harness/vendor/tomlc99/toml_json
# exit 139 (killed by SIGSEGV)
```

**Root cause (hypothesis, not yet confirmed against source):** `toml_parse`
appears to parse array values via unbounded recursive descent — one stack
frame per nesting level — with no depth limit. Bisected the crash boundary
on this machine: fine at depth 47,500, crashes by depth 48,750. Exact
threshold is stack-size-dependent, not a fixed constant in the library, so
depth 60,000 is used as a comfortable margin, not a precise minimum.

**Why this isn't in `adaptations.md`'s divergence table:** the ANTLR
grammar doesn't bound array nesting depth either — TOML.g4's array rule is
just as recursive. So this isn't a grammar-vs-library disagreement, it's a
straight memory-safety bug (stack exhaustion, likely reported as
stack-overflow / SIGSEGV under ASan too, worth confirming in Module 2).
Per the Module 1 plan, this gets carried forward to the Module 6 triage
pipeline rather than analyzed here.

**Status:** reproduced with a plain (non-sanitizer) build only. Needs
re-confirmation under the ASan/UBSan harness (Module 2) to get a proper
stack trace and crash signature before triage.

## 02_dotted_key_stackoverflow.toml

**Symptom:** `harness/build/toml_harness` (ASan/UBSan build) crashes with
`AddressSanitizer: stack-overflow` (exit 86) on a key with an extreme
number of dotted segments, e.g. `a.a.a.…k = 1`.

**Repro:**
```bash
source harness/sanitizer_env.sh
harness/build/toml_harness grammar/early_findings/02_dotted_key_stackoverflow.toml
# exit 86, ASan stack-overflow
```

**Root cause (confirmed against source):** `parse_keyval` (`toml.c:1106`)
handles an inline dotted key by recursing into itself at `toml.c:1138`,
once per dot, with **no depth guard**. The library *does* bound table-header
path depth ("max allowed is 10", `toml.c:1216`) but that check only guards
`[table.header]` paths — the inline dotted-key path is separate and
unbounded. One native stack frame per dot; deep enough exhausts the stack.

**Distinct from finding #01:** different recursing function
(`parse_keyval` vs `parse_array`) and different normalized stack
signature (`55628614cd6c` vs `939402a0547c`) — a genuinely separate bug,
not a repeat. Found by reading `toml.c` during Module-7b crash-hunting
planning, not by the fuzzing loop. See
`planning/hunting/step-01-second-crash-dotted-key.md`.

**Depth note:** the file uses depth 105,000 — comfortably above this
machine's ~90k crash threshold, but deliberately not deeper: past ~120k
the overflow becomes too violent for ASan to unwind a backtrace, which
would collapse its signature into the frameless "unparsed" bucket and
hide that it's a distinct bug.
