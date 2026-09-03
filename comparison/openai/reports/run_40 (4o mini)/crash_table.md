_Latest triaged run: `run_40`_ — **4 raw signature(s) → 3 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 151 | 180001 → 180001 B | deterministic (3/3 runs crashed) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 173 | 183483 → 183483 B | FLAKY (1/3 runs crashed) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 1 | 120006 → 15408 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 70 | 180001 → 180001 B | crashed every run (3/3) but signature unstable (2/3 matched) |
