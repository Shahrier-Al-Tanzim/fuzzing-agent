# Module 2 — Harness & Sanitizer Build

A single-input C driver for tomlc99, built with ASan + UBSan.

## Exit-code contract
| Code | Meaning |
|---|---|
| 0  | valid parse, full tree walk completed |
| 2  | well-formed rejection (message on stderr, prefixed `REJECT:`) |
| 64 | harness usage error — not a finding |
| 86 | sanitizer fired (set via ASAN/UBSAN_OPTIONS exitcode) |
| <0 | killed by a signal |

## Design notes
- The harness **walks the whole parsed tree** and converts every scalar,
  not just `toml_parse()`. Accessor and conversion paths are where much of
  tomlc99's pointer arithmetic lives.
- Walk recursion is capped at 200 so the *harness* can't stack-overflow and
  be mistaken for a library defect.
- Input capped at 1 MiB → code 64, so a pathological generator is visible
  rather than fatal.
- `-fno-sanitize-recover=all` so UBSan aborts instead of warning and
  continuing.
- `detect_leaks=0` — see sanitizer_env.sh for the rationale.

## Build & verify
    ./harness/build.sh
    ./harness/samples/run_samples.sh