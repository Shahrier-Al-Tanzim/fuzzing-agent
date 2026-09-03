_Latest triaged run: `run_49`_ — **3 raw signature(s) → 2 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 13 | 647907 → 647907 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 131 | 60013 → 16223 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 19 | 60540 → 60540 B | crashed every run (3/3) but signature unstable (0/3 matched) |
