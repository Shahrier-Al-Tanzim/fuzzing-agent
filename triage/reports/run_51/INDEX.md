# Crash triage index — run 51

6 unique signature(s) after deduplication, 5 distinct bug(s) after grouping by root cause (see the Bug column).

| Signature | Bug | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|---|
| `unparsed_timeout` | Bug 4: many-siblings O(n^2) hang | ? | 201 | 164905 B | no |
| `939402a0547c` | Bug 1: array-nesting stack overflow | stack-overflow | 272 | 20429 B | unstable-sig |
| `e857b4530c96` | Bug 1: array-nesting stack overflow | stack-overflow | 59 | 96008 B | unstable-sig |
| `55628614cd6c` | Bug 2: dotted-key stack overflow | stack-overflow | 11 | 180010 B | unstable-sig |
| `26e809dd9d85` | Bug 3: inline-table stack overflow | stack-overflow | 21 | 484649 B | unstable-sig |
| `f3095340ceab` | Bug 6: quoted-key dotted-key chain overflow | stack-overflow | 31 | 360031 B | unstable-sig |

Generated 2026-09-03T16:38:29.509264+00:00
