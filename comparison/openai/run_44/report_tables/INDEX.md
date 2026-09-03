# Crash triage index — run 44

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 47 | 198732 B | yes |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 23 | 160005 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 44 | 106153 B | yes |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 51 | 120005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 20 | 263092 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 14 | 342005 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 8 | 367623 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 44 | 28861 B | yes |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 11 | 180505 B | unstable-sig |

Generated 2026-09-02T22:20:49.796443+00:00
