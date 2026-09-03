_Latest triaged run: `run_37`_ — **9 raw signature(s) → 5 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `3db1e06f41e9` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 44 | 360005 → 360005 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `80953bb88ca2` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 116 | 160005 → 152005 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `af1d0280777e` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 39 | 360005 → 360005 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 161 | 200005 → 190005 B | deterministic (3/3 runs crashed) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 171 | 192382 → 192382 B | FLAKY (1/3 runs crashed) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 208 | 120005 → 22058 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 233 | 120005 → 40505 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 148 | 340005 → 214292 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `c04d038a7956` | quoted keys inside alternating nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 135 | 160005 → 160005 B | crashed every run (3/3) but signature unstable (2/3 matched) |
