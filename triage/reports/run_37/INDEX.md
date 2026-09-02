# Crash triage index — run 37

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 208 | 22058 B | yes |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 233 | 40505 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 171 | 192382 B | flaky |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 135 | 160005 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 148 | 214292 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 116 | 152005 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 161 | 190005 B | yes |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 39 | 360005 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 44 | 360005 B | unstable-sig |

Generated 2026-09-01T21:45:45.736743+00:00
