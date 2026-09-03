# Crash triage index — run 52

6 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 171 | 27787 B | unstable-sig |
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 136 | 158333 B | flaky |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 29 | 62851 B | unstable-sig |
| `f3095340ceab` | Bug 6: quoted-key dotted-key chain overflow | stack-overflow | 27 | 217816 B | unstable-sig |
| `e1e7b894bf33` | Bug 5: alternating array/inline-table overflow | stack-overflow | 2 | 314340 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 9 | 189341 B | yes |

Generated 2026-09-03T17:20:16.252093+00:00
