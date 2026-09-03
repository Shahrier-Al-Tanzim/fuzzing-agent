_Latest triaged run: `run_32`_

| Signature | Mechanism | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|
| `3db1e06f41e9` | alternating array/inline-table nesting | stack-overflow | 38 | 360012 → 360012 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `80953bb88ca2` | alternating array/inline-table nesting | stack-overflow | 144 | 160012 → 160012 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `af1d0280777e` | alternating array/inline-table nesting | stack-overflow | 38 | 360012 → 360012 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `55628614cd6c` | dotted keys | stack-overflow | 125 | 200005 → 180505 B | deterministic (3/3 runs crashed) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | ? | 183 | 184495 → 184495 B | FLAKY (1/3 runs crashed) |
| `939402a0547c` | nested arrays | stack-overflow | 194 | 120006 → 17071 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | stack-overflow | 242 | 121594 → 121594 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `26e809dd9d85` | nested inline tables | stack-overflow | 118 | 340012 → 340012 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `c04d038a7956` | quoted keys inside alternating nesting | stack-overflow | 138 | 160012 → 160012 B | crashed every run (3/3) but signature unstable (2/3 matched) |
