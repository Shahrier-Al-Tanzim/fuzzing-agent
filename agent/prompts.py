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