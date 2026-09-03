_Latest triaged run: `run_52`_ — **6 raw signature(s) → 5 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 136 | 158333 → 158333 B | FLAKY (2/3 runs crashed) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 171 | 96010 → 27787 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 29 | 98012 → 62851 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 9 | 220836 → 189341 B | deterministic (3/3 runs crashed) |
| `e1e7b894bf33` | unclassified | Bug 5: alternating array/inline-table overflow | stack-overflow | 2 | 314340 → 314340 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `f3095340ceab` | unclassified | Bug 6: quoted-key dotted-key chain overflow | stack-overflow | 27 | 281492 → 217816 B | crashed every run (3/3) but signature unstable (2/3 matched) |
