_Latest triaged run: `run_50`_ — **7 raw signature(s) → 6 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 32 | 618893 → 618893 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 202 | 420889 → 420889 B | deterministic (3/3 runs crashed) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 220 | 96010 → 32408 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 108 | 96010 → 48008 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 56 | 339281 → 276348 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `e1e7b894bf33` | unclassified | unclassified (e1e7b894bf33) | stack-overflow | 14 | 480544 → 456517 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `f3095340ceab` | unclassified | unclassified (f3095340ceab) | stack-overflow | 69 | 447502 → 425127 B | crashed every run (3/3) but signature unstable (2/3 matched) |
