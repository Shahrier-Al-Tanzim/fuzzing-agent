# Crash triage index — run 42

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 25 | 191986 B | flaky |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 23 | 324905 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 15 | 361316 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 41 | 291513 B | yes |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 76 | 136906 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 43 | 180505 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 48 | 152005 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 54 | 160005 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 51 | 15600 B | yes |

Generated 2026-09-02T21:55:53.802339+00:00
