# Crash triage index — run 39

9 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 315 | 120012 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 230 | 306862 B | unstable-sig |
| `80953bb88ca2` | Bug 5: alternating array/inline-table overflow | stack-overflow | 112 | 160013 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 176 | 166620 B | no |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 162 | 180505 B | yes |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 226 | 22058 B | yes |
| `c04d038a7956` | Bug 5: alternating array/inline-table overflow | stack-overflow | 135 | 144413 B | unstable-sig |
| `af1d0280777e` | Bug 5: alternating array/inline-table overflow | stack-overflow | 39 | 360012 B | unstable-sig |
| `3db1e06f41e9` | Bug 5: alternating array/inline-table overflow | stack-overflow | 49 | 360012 B | unstable-sig |

Generated 2026-09-01T23:54:37.536134+00:00
