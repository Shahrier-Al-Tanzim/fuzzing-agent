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

    