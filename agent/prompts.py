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
16. Many of the bugs in `tomlc99` are caused by pushing a SPECIFIC grammar
    production past the parser's depth limit. Identify the axes yourself
    by reading grammar/TomlParser.g4 directly - any production with
    recursion or with `*` / `+` quantifiers is a candidate stress axis,
    not because this prompt names them, but because the grammar does:
      * recursive productions: array : '[' array* ']' (deep array
                               nesting), inline_table : '{' pair* '}'
                               (deep inline-table nesting),
      * `+` quantifiers:      dotted_key : simple_key ('.' simple_key)+
                              (deep dotted-key chains), document :
                              expression (NL expression)+ (long flat
                              documents).
    Each axis has its OWN parser code path AND its OWN crash threshold -
    array nesting, inline-table nesting, dotted-key chains, and document-
    line counts each stress different parts of the parser. Push EVERY
    axis to its limit; missing any one means missing a bug class. A REAL
    FAILURE from a previous attempt: only some axes were wired into
    `toml_strategy`, so the missing ones never ran once.

    To reach EXTREME depth on any axis (hundreds or thousands of levels,
    as the feedback may request), recursive generation CANNOT do it.
    MEASURED FACT from previous attempts - no matter how heavily biased:
      * `st.lists(...)` with no size limit spreads SIDEWAYS into a bushy
        tree and exhausts Hypothesis's data budget at depth 2-3.
        Measured: max depth 3 over 15 draws.
      * Even forcing exactly one child per level (`min_size=1,
        max_size=1`), which is the correct chain shape, only reached
        depth ~13 over 15 draws - Hypothesis's own generation budget
        inherently resists deep recursion.

    So for extreme depth, build the structure DIRECTLY, not recursively.
    Draw a depth INTEGER, then construct the document so it actually has
    N levels of nesting on the chosen axis - repetition of opening /
    closing characters, iterative assembly, anything that produces a
    document the parser must walk depth N levels. The exact form is up
    to you; the CONSTRAINT is what matters: the generated string must
    really have N levels of nesting. The depth is the variable you
    control; how you reach it is your choice.

    SET `max_value` FROM THE DEPTH TARGET IN THE FEEDBACK, not from any
    worked example this prompt might have shown in earlier versions. A
    REAL FAILURE from a previous attempt: when this prompt used to show
    concrete example bounds, every iteration copied those numbers
    verbatim - depth then sat at exactly that ceiling for all five
    iterations, never reaching the depth where crashes actually fire.
    The feedback tells you what depth the parser crashes at on each
    axis; your job is to clear that bar. RAISE `max_value` to follow
    the feedback - never lower `min_value` below whatever keeps the
    draw above its own crash threshold.

    WHAT SITS AT EACH LEVEL MATTERS AS MUCH AS HOW DEEP THE NESTING
    GOES: two documents nested equally deep crash in different parser
    functions depending on what each level contains (bare vs quoted vs
    dotted keys, escaped strings, different value types). For at least
    one variant per axis, vary the CONTENT of each level so the parser
    takes a different code path than the bare-keys version. MEASURED
    FACT: the same alternating-nesting strategy with bare keys at every
    level vs QUOTED keys at every level crashes in DIFFERENT parser
    functions (the quoted version puts string-normalization on the stack
    at the moment it overflows), so each is a genuinely separate bug
    class, not just a variant.

    Keep deep branches inside a normal `key = value` line (rule 12/14 -
    a bare `[[[...]]]` alone is not a valid document), e.g.
    `f"deep = {draw(deep_strategy())}"`. Two hard limits: keep the
    whole document under 1 MB, and keep the deep branches a clear
    MINORITY of `toml_strategy`'s `one_of(...)` - deep branches together
    must be no more than ~1 in 5 of all branches, so the measured
    acceptance rate stays above the 20% floor. A higher fraction means
    most draws crash before the harness accepts them, so the strategy
    gets rejected before it ever runs - losing the very crashes it was
    built to find:
      Right:  toml_strategy = st.one_of(
                  *([document()] * 20),
                  deep_doc(strategy_a()), deep_doc(strategy_b()),
                  ...)
    IMPORTANT: still use `st.recursive` / `@composite` for ordinary
    nesting (rule 10). Direct construction is ONLY for the extreme-depth
    branch, not a replacement for real recursive structure everywhere.
17. ALSO generate documents with MANY SIBLING keys in ONE table (not
    nested - flat, side by side), as a second, DIFFERENT way to break
    the parser. MEASURED FACT: many TOML libraries (including `tomlc99`)
    look up every key with a linear scan through all existing keys, so
    adding N keys to the same table costs O(N^2) time overall. A few
    hundred KB of flat key=value lines is enough because the bug comes
    from COUNT of keys, not DEPTH of nesting.

    SET THE SIBLING COUNT FROM THE FEEDBACK, not from this prompt. If
    the feedback shows `many sibling keys (a hang, not a crash)` already
    triggering in the crash line, that axis is done - move on. If it is
    NOT triggering yet, push the count higher next iteration. Same
    logic as rule 16: don't pin to a number from this prompt, let the
    feedback steer it. A REAL FAILURE from a previous attempt: the
    worked-example bounds in this rule were copied verbatim and the
    count then sat at exactly that ceiling, never reaching the level
    where the timeout fires.

    Add this as another branch in `toml_strategy`'s `one_of(...)`,
    alongside the deep-nesting branch from rule 16 - they are two
    DIFFERENT bug classes (a stack overflow from nesting vs. a timeout
    from key count), so both are worth generating, not just one.
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

    