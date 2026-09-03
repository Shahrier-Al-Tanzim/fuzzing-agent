_Latest triaged run: `run_48`_ — **7 raw signature(s) → 6 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 8 | 200003 → 180503 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 112 | 173370 → 173370 B | DID NOT REPRODUCE (0/3) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 221 | 96008 → 18489 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 44 | 96013 → 72013 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 9 | 637515 → 575358 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `8a34ed52e713` | unclassified | unclassified (8a34ed52e713) | stack-overflow | 1 | 163570 → 160174 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `f3095340ceab` | unclassified | unclassified (f3095340ceab) | stack-overflow | 6 | 777110 → 777110 B | deterministic (3/3 runs crashed) |
