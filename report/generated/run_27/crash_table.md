_Latest triaged run: `run_27`_

| Signature | Mechanism | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|
| `3db1e06f41e9` | alternating array/inline-table nesting | stack-overflow | 52 | 360005 → 342005 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `80953bb88ca2` | alternating array/inline-table nesting | stack-overflow | 111 | 160005 → 137185 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `af1d0280777e` | alternating array/inline-table nesting | stack-overflow | 56 | 360005 → 342005 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `55628614cd6c` | dotted keys | stack-overflow | 152 | 200005 → 180505 B | deterministic (3/3 runs crashed) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | ? | 172 | 188444 → 188444 B | deterministic (3/3 runs crashed) |
| `939402a0547c` | nested arrays | stack-overflow | 174 | 120005 → 28505 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `e857b4530c96` | nested arrays | stack-overflow | 246 | 124233 → 124233 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | stack-overflow | 112 | 340005 → 323005 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `c04d038a7956` | quoted keys inside alternating nesting | stack-overflow | 131 | 160005 → 152005 B | deterministic (3/3 runs crashed) |
