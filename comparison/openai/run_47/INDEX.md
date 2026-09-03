# Crash triage index — run 47

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 113 | 96904 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 16 | 273608 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 68 | 18489 B | yes |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 45 | 181237 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 61 | 130329 B | yes |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 48 | 304008 B | yes |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 36 | 153551 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 20 | 314120 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 25 | 197761 B | yes |

Generated 2026-09-02T23:32:49.884141+00:00
