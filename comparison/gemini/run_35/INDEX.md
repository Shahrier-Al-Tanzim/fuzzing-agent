# Crash triage index — run 35

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 53 | 360005 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 122 | 160005 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 62 | 360005 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 122 | 180505 B | yes |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 125 | 170525 B | no |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 166 | 15600 B | unstable-sig |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 235 | 120005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 112 | 323005 B | unstable-sig |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 135 | 144405 B | unstable-sig |

Generated 2026-09-01T20:00:37.391441+00:00
