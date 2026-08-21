_Latest triaged run: `run_28`_

| Signature | Mechanism | Type | Occurrences | Size (orig → min) | Verified |
|---|---|---|---|---|---|
| `3db1e06f41e9` | alternating array/inline-table nesting | stack-overflow | 59 | 360005 → 360005 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `80953bb88ca2` | alternating array/inline-table nesting | stack-overflow | 127 | 160005 → 160005 B | deterministic (3/3 runs crashed) |
| `af1d0280777e` | alternating array/inline-table nesting | stack-overflow | 46 | 360005 → 360005 B | crashed every run (3/3) but signature unstable (1/3 matched) |
| `55628614cd6c` | dotted keys | stack-overflow | 158 | 200005 → 190005 B | crashed every run (3/3) but signature unstable (2/3 matched) |
| `unparsed_timeout` | many sibling keys (a hang, not a crash) | ? | 126 | 139747 → 139747 B | DID NOT REPRODUCE (0/3) |
| `939402a0547c` | nested arrays | stack-overflow | 201 | 120005 → 24440 B | deterministic (3/3 runs crashed) |
| `e857b4530c96` | nested arrays | stack-overflow | 252 | 120005 → 120005 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `26e809dd9d85` | nested inline tables | stack-overflow | 160 | 340005 → 306855 B | crashed every run (3/3) but signature unstable (0/3 matched) |
| `c04d038a7956` | quoted keys inside alternating nesting | stack-overflow | 156 | 160005 → 160005 B | crashed every run (3/3) but signature unstable (2/3 matched) |
