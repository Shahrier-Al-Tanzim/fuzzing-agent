# Crash triage index — run 40

4 unique signature(s) after deduplication, 3 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 173 | 183483 B | flaky |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 151 | 180001 B | yes |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 70 | 180001 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 1 | 15408 B | yes |

Generated 2026-09-02T21:02:31.311740+00:00
