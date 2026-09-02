# Crash triage index — run 36

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 198 | 17969 B | yes |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 36 | 360008 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 57 | 360008 B | unstable-sig |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 265 | 120008 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 113 | 160008 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 151 | 123814 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 167 | 180505 B | yes |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 128 | 306857 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 183 | 196639 B | yes |

Generated 2026-09-01T20:59:46.436160+00:00
