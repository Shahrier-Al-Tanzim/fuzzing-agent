# Crash triage index — run 38

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 280 | 60005 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 129 | 160005 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 182 | 24746 B | yes |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 156 | 180505 B | yes |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 133 | 160005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 136 | 340005 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 46 | 342005 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 177 | 186486 B | flaky |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 59 | 360005 B | unstable-sig |

Generated 2026-09-01T23:12:16.944435+00:00
