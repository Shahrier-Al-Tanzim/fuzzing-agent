_Latest triaged run: `run_51`_ — **6 raw signature(s) → 5 distinct bug(s)** after grouping by root cause (see the Bug column; multiple signatures can share one root cause, e.g. the same stack overflow captured mid-unwind at different points — see `agent/summarize.py`'s `BUG_FAMILIES` and `OBSERVATIONS.md` Case 9).

| Signature | Mechanism | Bug | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|---|
| `55628614cd6c` | dotted keys | Bug 2: dotted-key stack overflow | stack-overflow | 11 | 180010 → 180010 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | Bug 4: many-siblings O(n^2) hang | ? | 201 | 164905 → 164905 B | DID NOT REPRODUCE (0/3) |
| `939402a0547c` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 272 | 96008 → 20429 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `e857b4530c96` | nested arrays | Bug 1: array-nesting stack overflow | stack-overflow | 59 | 96008 → 96008 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | Bug 3: inline-table stack overflow | stack-overflow | 21 | 595020 → 484649 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `f3095340ceab` | unclassified | Bug 6: quoted-key dotted-key chain overflow | stack-overflow | 31 | 360031 → 360031 B | crashed every run (3/3) but signature unstable (2/3 matched) |
