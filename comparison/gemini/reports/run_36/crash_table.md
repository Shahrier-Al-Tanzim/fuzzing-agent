_Latest triaged run: `run_36`_ — **9 raw signature(s) → 5 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `3db1e06f41e9` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 57 | 360008 → 360008 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `80953bb88ca2` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 113 | 160009 → 160008 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `af1d0280777e` | alternating array/inline-table nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 36 | 360008 → 360008 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 167 | 200006 → 180505 B | deterministic (3/3 runs crashed) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 183 | 196639 → 196639 B | deterministic (3/3 runs crashed) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 198 | 120006 → 17969 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 265 | 120008 → 120008 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 128 | 340008 → 306857 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `c04d038a7956` | quoted keys inside alternating nesting | Bug 5: alternating array/inline-table overflow | stack-overflow | 151 | 160009 → 123814 B | crashed every run (3/3) but signature unstable (2/3 matched) |
