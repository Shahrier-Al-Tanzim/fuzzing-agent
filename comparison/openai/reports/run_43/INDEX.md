# Crash triage index — run 43

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 17 | 189962 B | flaky |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 13 | 180505 B | unstable-sig |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 53 | 128020 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 41 | 152005 B | yes |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 38 | 24440 B | yes |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 27 | 152684 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 8 | 360005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 34 | 323005 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 10 | 360005 B | unstable-sig |

Generated 2026-09-02T22:06:51.538468+00:00
