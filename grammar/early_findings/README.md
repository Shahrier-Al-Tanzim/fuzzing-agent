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
