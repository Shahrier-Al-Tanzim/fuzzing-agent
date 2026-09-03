# Crash triage index — run 45

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 107 | 191634 B | flaky |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 173 | 91208 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 129 | 32408 B | yes |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 64 | 160008 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 98 | 152008 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 95 | 180005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 80 | 320008 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 45 | 360008 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 26 | 360008 B | unstable-sig |

Generated 2026-09-02T22:55:30.252998+00:00
