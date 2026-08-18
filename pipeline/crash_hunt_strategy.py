"""Parametric crash-hunting strategies (Mode 1, no LLM).

Each strategy draws a single *depth* parameter and emits one structurally
extreme TOML document. The depth ranges are tuned per construct, empirically,
against harness/build/toml_harness on this machine so that:

  * every draw is already past that construct's crash threshold (a crash is
    reliable, not a lucky fluke), and
  * the input stays well under harness.max_input_bytes (1 MB), so it triggers
    a real stack overflow rather than the harness's oversized-input guard
    (exit 64, harness_error - not a finding), and
  * the *minimum* of each range sits in the "gentle overflow" zone where ASan
    can still unwind a parseable backtrace most of the time. This matters
    because Hypothesis's shrinker converges the crash toward the range minimum
    (see run_crash_hunt.py), so the kept/minimized reproducer is the most
    reliably-parseable depth, not the deepest.

Why depth is an explicit `st.integers` parameter rather than emergent from a
recursive `st.recursive` strategy: the balanced agent/ generator already does
emergent recursion, and its depth plateaus around 3 (Hypothesis biases toward
shallow structures). To reach the tens of thousands a stack overflow needs,
depth must be drawn directly - and doing so lets the shrinker report the
threshold depth as a bonus.

Byte budget (all < 1 MB at their range maxima):
  * deep_array        : 2 B/level  -> 100k levels ~= 200 KB
  * deep_dotted_key   : 2 B/level  -> 130k levels ~= 260 KB
  * deep_inline_table : 4 B/level  -> 115k levels ~= 460 KB

Each targets a *distinct* tomlc99 recursion (verified during planning):
  * deep_array        -> parse_array self-recursion            (toml.c:1057)
  * deep_dotted_key   -> parse_keyval self-recursion           (toml.c:1138)
  * deep_inline_table -> parse_keyval <-> parse_inline_table   (toml.c:961)
"""
from __future__ import annotations

from hypothesis import strategies as st

# Mirror harness.max_input_bytes so a campaign can assert it stays in range.
MAX_INPUT_BYTES = 1_048_576


@st.composite
def deep_array(draw) -> str:
    """`x = [[[ ... 1 ... ]]]` - nested arrays, parse_array recursion."""
    depth = draw(st.integers(min_value=60_000, max_value=100_000))
    return "x = " + ("[" * depth) + "1" + ("]" * depth)


@st.composite
def deep_dotted_key(draw) -> str:
    """`a.a.a. ... k = 1` - dotted-key chain, parse_keyval recursion."""
    depth = draw(st.integers(min_value=100_000, max_value=130_000))
    return ("a." * depth) + "k = 1\n"


@st.composite
def deep_inline_table(draw) -> str:
    """`x = {a={a= ... 1 ... }}` - nested inline tables, parse_inline_table
    <-> parse_keyval mutual recursion."""
    depth = draw(st.integers(min_value=85_000, max_value=115_000))
    return "x = " + ("{a=" * depth) + "1" + ("}" * depth)


@st.composite
def deep_mixed_nesting(draw) -> str:
    """`x = [{a= ... 1 ... }]` - arrays and inline tables alternating each
    level, not either construct alone. Confirmed a DISTINCT signature
    (af1d0280777e) from both deep_array and deep_inline_table, reproducing
    4/4 with parseable frames - the most stable of the four campaigns."""
    depth = draw(st.integers(min_value=60_000, max_value=80_000))
    return "x = " + ("[{a=" * depth) + "1" + ("}]" * depth)


# name -> strategy object. run_crash_hunt.py iterates this.
CRASH_HUNT_STRATEGIES = {
    "deep_array": deep_array(),
    "deep_dotted_key": deep_dotted_key(),
    "deep_inline_table": deep_inline_table(),
    "deep_mixed_nesting": deep_mixed_nesting(),
}
