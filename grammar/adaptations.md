# Grammar Adaptations: ANTLR TOML.g4 → tomlc99 @ 5221b3d

## Source
- Grammar: antlr/grammars-v4 `toml/TomlLexer.g4` + `TomlParser.g4`, fetched 2026-08-12, describes TOML v1.0.0
- Library: cktan/tomlc99 @ `5221b3d3d66c25a1dc6f0372b4f824f1202fe398` (2023-09-30)

## Method
Every construct in the ANTLR grammar files was exercised by a hand-written
sample and run through the pinned build's `toml_json` demo binary
(`harness/vendor/tomlc99/toml_json`, no sanitizers — this is a plain
build, sanitizers land in Module 2). Divergences below are observed
behavior, cross-checked against the actual lexer/parser rules in
`TomlLexer.g4` / `TomlParser.g4` (line numbers cited), not inferred from
the TOML spec or assumed.

`grammar/probe.sh` runs the full sample set and prints ACCEPT/REJECT per
file. Samples live in `sample_inputs/valid/` and `sample_inputs/invalid/`,
named by **what the ANTLR grammar says**, not by what tomlc99 does —
so a file under `invalid/` that comes back ACCEPT, or vice versa, is
itself the divergence signal.

## Divergence table

| # | Grammar construct | ANTLR says | tomlc99 does | Class | Evidence |
|---|---|---|---|---|---|
| 1 | Trailing comma in inline table: `{ a = 1, b = 2, }` | invalid — `inline_table_keyvals_non_empty` (TomlParser.g4:145-147) requires a `key EQUALS value` after every `COMMA`, so a comma cannot be followed by `}` | ACCEPT — parses cleanly, no error | **superset** | `invalid/06_trailing_comma_inline_table.toml` — exit 0, `{"x":{"a":...,"b":...}}` |
| 2 | Fractional seconds beyond microsecond precision: `.9999999999999999999` (19 digits) | valid — `SECFRAC: '.' DIGIT+` (TomlLexer.g4:95) places no upper bound on digit count | ACCEPT, but **silently truncates** to 3-digit (millisecond) precision with no error or warning | **variant** | `valid/06_frac_seconds_precision.toml` — exit 0, output `"1979-05-27T00:32:00.999-07:00"` (input had 19 nines, output has 3) |
| 3 | Integer one past `INT64_MAX`: `9223372036854775808` | valid — `DEC_INT: [+-]? (DIGIT \| (DIGIT_1_9 (DIGIT\|'_' DIGIT)+))` (TomlLexer.g4:82) is purely lexical, no magnitude bound | ACCEPT, but **silently re-typed**: `toml_json` reports `"type":"float"` for a value that is lexically an integer, instead of erroring or wrapping | **variant** | `valid/07_int_overflow.toml` — exit 0, `{"x":{"type":"float","value":"9223372036854775808"}}` |
| 4 | Leading-zero decimal integer: `007` | invalid — `DEC_INT` (TomlLexer.g4:82) only matches a lone `DIGIT` or `DIGIT_1_9` followed by more digits; `0` followed by more digits matches neither alternative | `toml_parse()` itself **accepts** `007` as an untyped raw value (no parse-time `ERROR:` line) — but every typed converter tomlc99 offers (`toml_rtoi`, `toml_rtod`, `toml_rtos`, `toml_rtob`, `toml_rtots`) then rejects it, so `toml_json`'s demo-side type dispatch falls through to its `else` branch and aborts with `unknown type` before finishing the JSON output | **variant** — reveals a two-layer API split: `toml_parse` succeeding does **not** mean the value is usable; a later `toml_rto*` call can still fail on input the parser silently let through | `invalid/07_leading_zero_int.toml` — exit 1, stdout `{"x":` (truncated, malformed), stderr `unknown type` (see `harness/vendor/tomlc99/toml_json.c:107`) — distinct from every other REJECT sample, which prints a clean single-line `ERROR: line N: ...` and exits without partial stdout |
| 5 | Array nesting depth (`[[[…]]]`) | grammar places no depth bound either (recursive rule), so this is not strictly a grammar-vs-spec mismatch | **Stack overflow (SIGSEGV)** at ~48,000+ levels of nesting on this machine's default 8 MB stack — recursive-descent parsing, one native stack frame per nesting level, no depth guard | **crash, not a spec divergence** — logged separately | `grammar/early_findings/01_array_nesting_stackoverflow.toml` (depth 60,000) — exit 139. Bisected boundary: depth 47,500 OK, depth 48,750 crashes. See `grammar/early_findings/README.md`. |

Classes:
- **subset** — library rejects something the grammar allows
- **superset** — library accepts something the grammar forbids
- **variant** — library accepts it but with different semantics

## Consequences for generation
- Divergence #1 → generate trailing commas in inline tables deliberately.
  It's spec-forbidden-and-grammar-forbidden but tomlc99 silently accepts
  it, so it's free surface area the parser wasn't meant to handle — good
  for exercising code paths a spec-conformant test suite would never hit.
- Divergence #2 → generate over-long fractional seconds deliberately.
  Silent truncation (not an error) means downstream code that trusts the
  parsed timestamp value can silently get a different sub-second time than
  what was written — a correctness bug candidate even without a crash.
- Divergence #3 → generate integers at and past `INT64_MAX`/`INT64_MIN`
  deliberately. The int→float reclassification is exactly the kind of
  type-confusion boundary that's worth hammering: any C code downstream
  that branches on "is this an int or a float" based on tomlc99's raw
  string alone, without calling `toml_rtoi` first, will get surprised.
- Divergence #4 → generate leading-zero integers deliberately, and make
  sure the Hypothesis-driven harness in Module 2 **calls the typed
  `toml_rto*` accessors**, not just `toml_parse()`, when checking whether
  an input was "accepted." Treating `toml_parse() == 0` as "valid TOML"
  would silently misclassify this whole class of input as accepted when
  it's actually unusable.
- Divergence #5 → not a generation-strategy concern (depth isn't part of
  the value grammar in a way Hypothesis's `recursive()` strategy needs
  special-casing beyond a sane `max_leaves`), but the reproducer is
  reserved for Module 6's crash triage — this is the first confirmed
  memory-safety-adjacent bug in the project, worth re-running under ASan
  once the sanitizer harness exists in Module 2.

## Deliberate scope cuts
Constructs checked and found **non-divergent** — probed to rule them out,
not skipped:
- **`inf`/`nan` floats** (`INF`/`NAN`, TomlLexer.g4:74-75) — grammar valid,
  tomlc99 accepts (`valid/01_scalars.toml`, already in the original
  sample set). No divergence at this pinned commit; older tomlc99
  versions reportedly vary here, so worth re-checking if the pinned hash
  ever changes.
- **Newlines inside inline tables** (`{ a = 1,\nb = 2 }`) — grammar
  invalid (`INLINE_TABLE_WS: WS -> skip` only skips space/tab, TomlLexer.g4:108,
  and `WS` itself is `[ \t]+`, TomlLexer.g4:26 — no newline in the skip
  set means a literal newline can't be lexed inside `{ }`). tomlc99
  rejects it too, with a specific message (`newline not allowed in inline
  table`) rather than a generic syntax error — conformant, not a
  divergence. (`invalid/08_newline_inline_table.toml`)
- **Unicode bare keys** (`héllo = 1`) — grammar invalid
  (`UNQUOTED_KEY: (ALPHA|DIGIT|'-'|'_')+` where `ALPHA: [A-Za-z]`,
  TomlLexer.g4:37-38,50 — ASCII only). tomlc99 rejects it too, though with
  a confusing diagnostic (`missing =`, since the lexer stops consuming at
  the non-ASCII byte and the parser sees a truncated key with no `=`
  after it) rather than an illegal-character message. Correctly rejected,
  so not generated as a divergence-hunting case, but noted because the
  error message would be misleading if surfaced to a user during triage.
  (`invalid/09_unicode_bare_key.toml`)
- **Dotted keys at top level** (`a.b.c = 1`, `dotted_key`,
  TomlParser.g4:66-68) — grammar valid, tomlc99 accepts and expands it
  into nested tables correctly. Conformant. (`valid/08_dotted_key_top_level.toml`)
- **Duplicate keys inside inline tables** (`{ a = 1, a = 2 }`) — not part
  of the original 8-point checklist, added while probing #1, since
  trailing-comma parsing touches the same code path. tomlc99 correctly
  rejects with `key exists`, matching the top-level duplicate-key
  behavior already covered by `invalid/02_duplicate_key.toml`. Comments
  were still not varied — no plausible memory-safety surface, low value
  per generated example.
