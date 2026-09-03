# Crash triage index — run 46

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 41 | 320008 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 51 | 160008 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 33 | 160016 B | unstable-sig |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 77 | 96008 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 34 | 203543 B | yes |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 11 | 360008 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 30 | 180505 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 14 | 360008 B | unstable-sig |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 54 | 15020 B | yes |

Generated 2026-09-02T23:17:33.655147+00:00
