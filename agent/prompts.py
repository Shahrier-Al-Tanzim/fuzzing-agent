"""Prompt templates. The refine prompt lives in Module 5.

Prompt engineering notes, since the report has to justify these:

  * The output contract (one fenced block, one module-level name) is stated
    three times - in the system prompt, in the rules, and in the closing
    line. A 7B model drops constraints stated once.
  * `st.recursive` / `@composite` is *required*, not suggested: the
    assignment explicitly grades whether recursion was flattened.
  * The edge-case list is enumerated rather than described. "Cover edge
    cases" produces nothing; a numbered list produces roughly the list.
  * Imports are restricted, and the reason is stated. The model is being
    exec'd - see validator.py gate 3.
"""
from __future__ import annotations

from agent.grammar_context import grammar_context

SYSTEM_PROMPT = (
    "You are a Python testing expert who writes Hypothesis strategies. "
    "You reply with exactly one fenced Python code block and nothing else - "
    "no explanation before or after it."
)

STRATEGY_CONTRACT = """\
OUTPUT CONTRACT - your reply is rejected automatically if it breaks these:
1. Reply with exactly ONE ```python fenced code block. No prose outside it.
2. The module must define a module-level variable named exactly:
       toml_strategy
   It must be a Hypothesis SearchStrategy that generates `str` values.
3. Allowed imports ONLY:
       from hypothesis import strategies as st
       from hypothesis.strategies import composite
   Do NOT import os, sys, subprocess, pathlib, random, or anything else.
4. No file I/O, no network, no printing, no `if __name__ == "__main__"`.
5. Every generated value must be a Python `str` holding TOML text.
6. If you use @composite, MUST import it and MUST call the function.
   Example (correct):
   ```python
   from hypothesis import strategies as st
   from hypothesis.strategies import composite

   @composite
   def my_strategy(draw):
       return draw(st.text())

   toml_strategy = my_strategy()  # Call it to get the strategy object
   ```
7. Common mistakes to avoid - these are REAL ERRORS from previous attempts:
   - `st.datetimes()` takes NO `formats` argument. It does not exist. If you
     need a date/time string, build it yourself, e.g.:
       st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
           .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")
   - NEVER combine strategies with `+`. Strategies do not support addition.
     To pick one of several strategies use `st.one_of(a, b, c)` or `a | b | c`.
     To join strings use `.map(lambda parts: "".join(parts))`, not `part1 + part2`.
   - Every `.map(fn)` callback receives exactly ONE argument: the value drawn
     from the strategy it is called on. `st.tuples(a, b).map(lambda x: ...)`
     receives ONE tuple `x`, not two separate arguments. Do not write
     `.map(lambda a, b: ...)` on a single strategy - unpack inside instead:
     `.map(lambda pair: f"{pair[0]}={pair[1]}")`.
8. EVERY item you pass to `"".join(...)` or f-string interpolation MUST
   already be a `str`. This is a REAL ERROR from a previous attempt:
   - `st.integers()` and `st.floats()` return raw `int`/`float`, NOT `str`.
     Convert them before joining:
       st.integers(...).map(str)          # NOT: st.integers(...) alone
       st.floats(...).map(str)            # NOT: st.floats(...) alone
     Wrong:  st.one_of(st.integers(), st.floats(), st.text())  -> then
             ", ".join(elements) crashes with
             "TypeError: sequence item 0: expected str instance, int found"
     Right:  st.one_of(st.integers().map(str), st.floats().map(str), st.text())
   - Calling a @composite-decorated function WITHOUT `draw(...)` around it
     gives you the strategy object itself, not a value. This is a REAL ERROR:
       tables = [table_value() for _ in range(n)]   # WRONG - list of strategies
       "\\n".join(tables)  # crashes: "expected str instance, LazyStrategy found"
     Right:
       tables = [draw(table_value()) for _ in range(n)]   # draw() each one
   - Keep the shape a function returns consistent with what calls it expect.
     If `table()` returns a flat list of (key, value) pairs, the code that
     consumes it must not assume it returns `(name, list_of_pairs)` instead -
     mismatched shapes cause errors like "'float' object is not subscriptable"
     several calls later, far from the actual mistake.
9. NEVER use `.filter(lambda x: x.startswith(...))`, `.filter(lambda x:
   x.isidentifier())`, or any `.filter()` that checks the *shape* of random
   text. A REAL FAILURE from a previous attempt: `st.text(...).filter(lambda
   x: x.startswith('"') and x.endswith('"'))` - random text almost never
   happens to start AND end with a specific character, so Hypothesis
   silently exhausts its retry budget and stops after ~40-150 examples
   instead of the requested amount, with no error at all - just far fewer
   examples than asked for. Build the shape directly instead of filtering
   for it:
     Wrong:  st.text(min_size=2, max_size=10)
                 .filter(lambda x: x.startswith('"') and x.endswith('"'))
     Right:  st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"')
   `.filter()` is for excluding rare, genuinely-random edge cases (e.g. "not
   empty"), never for constructing a specific format - use `.map()` for that.
10. Containers MUST be able to genuinely contain themselves, not just
    scalars. This is a REAL FAILURE from a previous attempt - it used
    `@composite` and looked recursive, but never actually nested:
      Wrong:  @composite
              def array(draw):
                  # only ever draws scalars/pairs, never array() itself
                  elements = draw(st.lists(st.one_of(pair(), value())))
                  return f"[{', '.join(elements)}]"
    That produces arrays that can NEVER contain another array - every
    generated document stays at nesting depth 1 forever, however many
    iterations run. An array's element strategy MUST include the array
    strategy itself as one of its options:
      Right:  @composite
              def array(draw):
                  elements = draw(st.lists(
                      st.one_of(value(), array(), inline_table())))
                  return f"[{', '.join(elements)}]"
    Use `st.recursive(...)`'s own depth control (or a small manual depth
    counter passed through `draw`) to keep this from recursing forever -
    but it must be able to recurse at all. The grammar rewards deep
    nesting specifically; a flat container never reaches it.
11. `st.dates()` and `st.times()` take `min_value`/`max_value` ONLY - not
    `min_date`/`max_date`, not `min_time`/`max_time`. Both REAL ERRORS from
    previous attempts:
      Wrong:  st.dates(min_value='1970-01-01', max_value='2100-12-31')
              # crashes: Expected date but got min_value='1970-01-01' (type=str)
      Wrong:  st.times(min_time='00:00:00', max_time='23:59:59')
              # crashes: times() got an unexpected keyword argument 'min_time'
    `min_value`/`max_value` also need real `date`/`time` objects, not
    strings - and `datetime`/`date`/`time` cannot be imported anyway (rule
    3 only allows importing from `hypothesis`). So do NOT use
    `st.dates()`/`st.times()`/`st.datetimes()` at all. Build date/time
    strings directly from integers instead, the same way rule 7 already
    shows for a full timestamp:
      Right:  st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
                  .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}")
12. EVERY top-level line in `document()` MUST be one of exactly three
    things: a `key = value` pair, a `[table]` header, or a `[[array_table]]`
    header. NEVER a bare array or bare inline table on its own line. This
    is a REAL FAILURE from a previous attempt - `document()` mixed
    `array()`/`inline_table()` directly into its own top-level choices:
      Wrong:  @composite
              def document(draw):
                  elements = draw(st.lists(
                      st.one_of(pair(), table(), array(), inline_table())))
                  return "\\n".join(elements)
      # produces invalid lines like a bare "[14:36:03, true]" or bare "{}"
      # sitting on their own with no key - not valid TOML at any depth.
    `array()` and `inline_table()` are VALUES. They may only appear on the
    right-hand side of a `key = value` pair (which is what `pair()`/`value()`
    are for), never as one of `document()`'s own top-level choices:
      Right:  @composite
              def document(draw):
                  elements = draw(st.lists(st.one_of(pair(), table())))
                  return "\\n".join(elements)
    Arrays and inline tables still get exercised at any depth - just always
    reached through `pair()` -> `value()`, never placed at the document's
    own top level directly.
13. `[table]` and `[[array_table]]` header NAMES must be built with the
    SAME function you use for regular keys, never raw `st.text()` directly.
    This is a REAL FAILURE from a previous attempt, repeated identically
    across 5 separate generations - `table()` used unrestricted text with
    no quoting at all:
      Wrong:  @composite
              def table(draw):
                  return draw(st.one_of(
                      st.text(min_size=1, max_size=10).map(lambda x: f"[{x}]"),
                      st.text(min_size=1, max_size=10).map(lambda x: f"[[{x}]]")))
      # produces invalid headers like "[[\\x9f7]]" or "[\\u8862@\\u00b6\\u00c0]" -
      # unquoted keys may ONLY contain ASCII letters/digits/_/- ; anything
      # else (control characters, non-ASCII, punctuation, spaces) MUST be
      # quoted, exactly like a regular key already has to be.
    Reuse `key()` (or `dotted_key()`) for the header name instead of
    inventing a second, unrestricted way to generate one:
      Right:  @composite
              def table(draw):
                  return draw(st.one_of(
                      key().map(lambda k: f"[{k}]"),
                      key().map(lambda k: f"[[{k}]]")))
    A document alternates between `pair()` and `table()` roughly evenly, so
    an unquoted `table()` silently invalidates a large share of every
    generated document - this is a common, easy-to-miss cause of low
    acceptance rate that isn't a crash or an API mistake at all.
14. IF the feedback below asks you to push depth into the thousands, a
    balanced `st.one_of(value(), array(), inline_table())` CANNOT get there -
    each level only has roughly a 1-in-3 chance of recursing again, so the
    probability of reaching depth 1000+ is astronomically small even across
    500 examples. This was a REAL FAILURE from a previous attempt: depth
    stayed stuck at 3 for 5 straight iterations despite repeated requests to
    increase it, because nothing in the strategy actually favored recursion
    over stopping. Two correct techniques, use at least one:
    (a) Bias the choice by repeating the recursive option in `one_of()`:
      Right:  @composite
              def array(draw):
                  elements = draw(st.lists(
                      st.one_of(array(), array(), array(), array(), value())))
                  return f"[{', '.join(elements)}]"
      # array() listed 4x vs value() once -> recursion is drawn ~4x more
      # often than stopping, so depth grows instead of collapsing early.
    (b) Thread an explicit counter through `draw`, and ONLY stop recursing
        once it passes a high threshold - the counter MUST actually be
        incremented on the recursive call itself, not just declared:
      Wrong:  @composite
              def array(draw, depth=0):
                  # depth is never passed forward - every recursive call
                  # silently resets to depth=0, so the check below can
                  # never fire. A REAL FAILURE from a previous attempt.
                  if depth >= 12:
                      return draw(value())
                  return draw(st.one_of(value(), array()))
      Right:  @composite
              def array(draw, depth=0):
                  if depth >= 20000:
                      return draw(value())
                  return draw(st.one_of(
                      value(),
                      array(depth=depth + 1), array(depth=depth + 1),
                      array(depth=depth + 1), array(depth=depth + 1)))
      # depth=depth+1 is passed on every recursive call, so the counter
      # genuinely advances and the threshold is reachable.
    Whichever technique you use, keep a SECOND, balanced/shallow variant
    (as in earlier rules) for grammar breadth. BUT never expose a bare
    `array()`/`inline_table()`/`dotted_key()`/raw-number/raw-string
    strategy directly inside the final `toml_strategy`'s own `one_of()` -
    every branch of `toml_strategy` MUST still produce a COMPLETE document
    (one or more `key = value` / `[table]` / `[[array_table]]` lines), the
    same rule 12 already requires inside `document()`. This is a REAL
    FAILURE from a previous attempt - acceptance collapsed from 42% to 7%
    in one iteration because `toml_strategy` was built like this:
      Wrong:  toml_strategy = st.one_of(
                  document(), document(),
                  array(), dotted_key(), ml_basic_string(),        # bare
                  st.integers(...).map(lambda x: f"0x{x:x}"))      # bare
      # a raw array()/dotted_key()/hex-number AS THE ENTIRE FILE is not
      # valid TOML at any depth - TOML requires key=value/table lines,
      # never a bare value alone. 12 of 17 branches here produced instant
      # "missing =" rejects.
    The depth-seeking recursive strategy still only ever belongs inside
    `pair()`'s value position (via `value()`, exactly as rule 12 already
    routes `array()`/`inline_table()`) - never as a second, separate
    top-level option next to `document()`:
      Right:  toml_strategy = st.one_of(document(), document_depth_biased())
      # where document_depth_biased() is document()'s own shape (pair()/
      # table() lines) but pair() draws from the depth-biased array()/
      # inline_table() instead of the shallow one - still a full document,
      # every line still has its own `key =`.
15. `key()` MUST restrict its unquoted branch to a fixed alphabet, and any
    quoted key/string branch MUST exclude the quote character and control
    characters (including newline) from what it wraps in quotes. Two REAL
    FAILURES from previous attempts, both from unrestricted `st.text()`:
      Wrong:  st.text(min_size=1, max_size=10).map(lambda x: x)  # unquoted
      # produced literal keys like `[»\x1aî(\U0008e78b!v9×]` - unquoted
      # TOML keys may ONLY contain ASCII letters/digits/_/-, nothing else.
      Wrong:  st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"')
      # produced `"\\nDJ" = 0` - st.text() with no alphabet restriction can
      # generate a literal, unescaped newline character. A raw newline
      # inside a basic string breaks TOML's single-line string syntax
      # outright (only a triple-quoted \"\"\"...\"\"\" string may span
      # lines) - this doesn't just reject that one value, it corrupts line
      # counting for everything after it in the document.
    Fix by restricting the alphabet directly (never `.filter()` - rule 9
    already bans filtering for shape):
      Right:  import string
              UNQUOTED_KEY_CHARS = string.ascii_letters + string.digits + "-_"
              st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
                  # unquoted branch - safe by construction
              st.text(alphabet=string.printable.replace('"', '').replace("\\\\", "")
                       .replace("\\n", "").replace("\\r", ""),
                       min_size=1, max_size=10).map(lambda x: f'"{x}"')
                  # quoted branch - excludes the quote char, backslash, and
                  # newline/carriage-return from what's wrapped in quotes
    Apply this to every place raw `st.text()` gets wrapped in quotes or
    used unquoted as a key - not just `key()`, also any inline ad-hoc key
    building inside `inline_table()`/`dotted_key()` if it doesn't already
    call `key()`.
"""

SEED_TEMPLATE = """\
Write a Hypothesis strategy that generates TOML documents for fuzzing the
C library `tomlc99`.

{grammar_context}

## Requirements

- Use `st.recursive(...)` or `@composite` for the recursive parts of the
  grammar (arrays inside arrays, inline tables inside arrays, nested
  tables). Do NOT flatten recursion to a fixed depth of one or two.
- Build the document from composable pieces: keys, scalar values, arrays,
  inline tables, standard tables, array-of-tables. Compose them; do not
  emit one giant hardcoded template.
- Explicitly cover these edge cases:
  1. empty containers: `[]`, `{{}}`, and an empty document
  2. deep nesting of arrays and inline tables
  3. duplicate keys, both at top level and inside inline tables
  4. extreme numbers: 0, -0, INT64 max/min, values past INT64 range,
     leading zeros, `inf`, `-inf`, `nan`, exponents, underscores in digits
  5. strings: escape sequences (`\\n`, `\\t`, `\\"`, `\\\\`, `\\uXXXX`),
     invalid escapes, unicode above the BMP, literal and multi-line strings
  6. near-valid but malformed: trailing commas, missing `=`, unclosed
     brackets and quotes, newlines inside inline tables
- Bias toward the documented divergences above - those are known-weak spots.
- Keep generated documents small enough to stay well under 1 MB.

{contract}

Reply now with only the ```python block."""


def build_seed_prompt() -> str:
    return SEED_TEMPLATE.format(
        grammar_context=grammar_context(),
        contract=STRATEGY_CONTRACT,
    )


REFINE_TEMPLATE = """\
You are improving an existing Hypothesis strategy that fuzzes the C library
`tomlc99`. Below are the grammar, the current strategy, and measured results
from running it.

{grammar_context}

## Current strategy (iteration {prev_iteration})

```python
{current_code}
```

{feedback}

## Your task

Produce a REVISED strategy that addresses the priority list above. Keep what
is working - do not rewrite from scratch, and do not drop constructs that are
already being generated successfully. Keep using `st.recursive`/`@composite`
for recursive productions.

{contract}

Reply now with only the ```python block."""


def build_refine_prompt(current_code: str, feedback: str,
                        prev_iteration: int) -> str:
    return REFINE_TEMPLATE.format(
        grammar_context=grammar_context(),
        current_code=current_code,
        feedback=feedback,
        prev_iteration=prev_iteration,
        contract=STRATEGY_CONTRACT,
    )

    
    
#     16. To reach EXTREME nesting depth (hundreds or thousands of levels, as the
#     feedback may request), do NOT try to get there by recursion at all.
#     MEASURED FACT from previous attempts - recursive generation cannot do
#     it, no matter how heavily biased:
#       * `st.lists(...)` with no size limit averages ~50-90 elements, so a
#         recursive strategy spreads SIDEWAYS into a huge bushy tree and
#         exhausts Hypothesis's data budget at depth 2-3. Measured: max
#         depth 3 over 15 draws.
#       * Even forcing exactly one child per level (`min_size=1,
#         max_size=1`), which is the correct chain shape, only reached
#         depth 13 over 15 draws - Hypothesis's own generation budget
#         inherently resists deep recursion.
#     So for extreme depth, draw the depth as an INTEGER and build the
#     string directly by repetition - no recursion involved:
#       Right:  @composite
#               def deep_array(draw):
#                   n = draw(st.integers(min_value=60_000, max_value=100_000))
#                   return "[" * n + "1" + "]" * n
#       Right:  @composite
#               def deep_inline_table(draw):
#                   n = draw(st.integers(min_value=85_000, max_value=115_000))
#                   return "{a=" * n + "1" + "}" * n
#       Right:  @composite
#               def deep_dotted_key(draw):
#                   n = draw(st.integers(min_value=100_000, max_value=130_000))
#                   return "a." * n + "k"      # use as a KEY, not a value
#       Right:  @composite
#               def deep_mixed_nesting(draw):
#                   n = draw(st.integers(min_value=60_000, max_value=80_000))
#                   return "[{a=" * n + "1" + "}]" * n
#       Right:  @composite
#               def deep_quoted_mixed(draw):
#                   n = draw(st.integers(min_value=20_000, max_value=45_000))
#                   return '[{"k"=' * n + "1" + "}]" * n
#     THE FIVE SHAPES NEED DIFFERENT `min_value`s, and the numbers above are
#     MEASURED crash thresholds - do not flatten them to one shared floor.
#     Each construct overflows the parser's stack at its own depth: arrays at
#     roughly 48,000 levels, inline tables at roughly 80,000, dotted keys at
#     roughly 90,000-100,000. A shared low floor (e.g. 1,000 for all of them)
#     wastes most draws: a dotted key generated at depth 20,000 is five times
#     too shallow to do anything at all, which is a REAL FAILURE from previous
#     runs - the array shape crashed 120 times while the dotted-key shape
#     crashed only 3 times, purely because they shared one floor that suited
#     only the array.
#     `deep_mixed_nesting` is NOT a duplicate of the other three - it
#     alternates an array and an inline table at EVERY level, which drives a
#     different chain of parser functions (array -> inline table -> key/value
#     -> array, cycling) than either construct nested in itself. It therefore
#     crashes with a different stack signature and counts as a separate bug.
#     Generating only the three "pure" shapes misses it entirely.
#     `deep_quoted_mixed` is the same alternating nesting but with a QUOTED
#     key (`"k"`) at every level instead of a bare one. MEASURED FACT: this
#     single change moves the crash into a different parser function - a
#     quoted key has to be unescaped before it can be stored, so the
#     string-normalization code sits on the stack at the moment it overflows,
#     producing a stack signature none of the other four shapes ever produce.
#     WHAT SITS AT EACH LEVEL MATTERS AS MUCH AS HOW DEEP THE NESTING GOES:
#     two documents nested equally deep crash in different functions depending
#     on what each level contains. Note its depth range is deliberately LOWER
#     than the others (20,000-45,000) - a quoted key does more work per level,
#     so the stack runs out sooner; going deeper here just crashes earlier in
#     a way that hides this signature. So vary the CONTENT of each level
#     (bare vs quoted vs dotted keys, values needing escape processing), not
#     only the depth.
#     SET `max_value` FROM THE DEPTH TARGET IN THE FEEDBACK, not from this
#     example. A REAL FAILURE from a previous attempt: the numbers above were
#     copied verbatim as `max_value=5000` and depth then sat at exactly
#     4999-5000 for all five iterations - the generator never went past the
#     example's own ceiling, so it never reached the depth where anything
#     interesting happens. If the feedback asks for 30000+, `max_value` must
#     be at least 30000; if it asks for 90000+, at least 90000. Widen the
#     range by RAISING `max_value`, never by lowering `min_value` below the
#     per-shape floor given above - those floors are what make each draw land
#     above its own crash threshold.
#     Use ALL FIVE shapes, not just one - another REAL FAILURE: a previous
#     attempt defined `deep_inline_table` and `deep_dotted_key` but wired only
#     `deep_array` into `toml_strategy`, so two of the three never ran once.
#     Each shape stresses a different part of the parser, so include a branch
#     for each of the five in the final `st.one_of(...)`.
#     Keep every one of these inside a normal `key = value` line (rule 12/14
#     - a bare `[[[...]]]` alone is not a valid document), e.g.
#     `f"deep = {draw(deep_array())}"`. Two hard limits: keep the whole
#     document under 1 MB, and keep the deep branches a clear MINORITY of
#     `toml_strategy`'s `one_of(...)`. Concretely: list the five deep shapes
#     ONCE each (5 branches total) against AT LEAST 20 ordinary `document()`
#     branches, i.e. deep shapes together must be no more than ~1 in 5 of all
#     branches:
#       Right:  toml_strategy = st.one_of(
#                   *([document()] * 20),
#                   deep_doc(deep_array()), deep_doc(deep_inline_table()),
#                   deep_doc(deep_dotted_key()), deep_doc(deep_mixed_nesting()),
#                   deep_doc(deep_quoted_mixed()))
#       # where deep_doc(s) wraps the deep string in a `key = value` line
#     This ratio matters for a non-obvious reason: a document that crashes the
#     parser does not count as "accepted", and with the high per-shape floors
#     above almost EVERY deep draw now crashes. If deep branches are more than
#     a small minority, the measured acceptance rate falls below the 20% floor
#     and the whole strategy gets rejected before it ever runs - losing the
#     very crashes it was built to find.
#     IMPORTANT: still use `st.recursive`/`@composite` for ordinary nesting
#     (rule 10) - this integer-repetition trick is ONLY for the extreme-depth
#     branch, not a replacement for real recursive structure everywhere.
# 17. ALSO generate documents with MANY SIBLING keys in ONE table (not nested
#     - flat, side by side), as a second, DIFFERENT way to break the parser.
#     MEASURED FACT: `tomlc99` looks up every key with a linear scan through
#     all existing keys, so adding N keys to the same table costs O(N^2) time
#     overall. Confirmed directly against the harness: 5,000 sibling keys
#     took 0.74s (fine), but 15,000+ sibling keys took over 5 seconds and hit
#     the per-input timeout - which the assignment counts as a finding, same
#     as a crash. This needs far fewer bytes than deep nesting (a few hundred
#     KB, not tens of thousands of nesting levels) because it comes from
#     COUNT of keys, not DEPTH of nesting:
#       Right:  @composite
#               def many_siblings(draw):
#                   n = draw(st.integers(min_value=10_000, max_value=60_000))
#                   lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
#                   return "\\n".join(lines)
#     Add this as another branch in `toml_strategy`'s `one_of(...)`, alongside
#     the deep-nesting branch from rule 16 - they are two DIFFERENT bug
#     classes (a stack overflow from nesting vs. a timeout from key count),
#     so both are worth generating, not just one.
