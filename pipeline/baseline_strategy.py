"""Baseline Hypothesis strategies - deliberately grammar-unaware.

Three tiers, so the baseline produces a meaningful comparison rather than
just noise:

  random_text     - arbitrary unicode. Should be ~100% rejected. Establishes
                    that a dumb generator finds nothing, which is the whole
                    argument for the grammar-seeded approach.
  toml_ish_text   - characters drawn from TOML's alphabet only. Still
                    ~100% rejected, but proves rejection isn't merely an
                    encoding artifact.
  keyvalue_lines  - actual `key = value` lines. Should be mostly accepted,
                    and is what proves the ACCEPT path of the pipeline works
                    end to end. Without this tier a 0% acceptance rate is
                    ambiguous: broken generator, or broken runner?

That third tier is the real point. A baseline that only ever produces
rejections cannot distinguish "the pipeline works and the generator is bad"
from "the pipeline is broken".
"""
from __future__ import annotations

from hypothesis import strategies as st

# --- tier 1: arbitrary text ------------------------------------------------
random_text = st.text(min_size=0, max_size=200)

# --- tier 2: TOML alphabet, no structure -----------------------------------
TOML_ALPHABET = "abcXYZ0123456789 \t\n=[]{}\"'.,#-_+:"
toml_ish_text = st.text(alphabet=TOML_ALPHABET, min_size=0, max_size=200)

# --- tier 3: plausible key/value lines -------------------------------------
bare_key = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=1,
    max_size=12,
)

simple_value = st.one_of(
    st.integers(min_value=-1000, max_value=1000).map(str),
    st.booleans().map(lambda b: "true" if b else "false"),
    st.text(alphabet="abcXYZ 0123456789", max_size=20).map(lambda s: f'"{s}"'),
    st.floats(allow_nan=False, allow_infinity=False, width=32).map(repr),
)

keyvalue_lines = st.lists(
    st.tuples(bare_key, simple_value).map(lambda kv: f"{kv[0]} = {kv[1]}"),
    min_size=0,
    max_size=10,
).map("\n".join)


BASELINE_STRATEGIES = {
    "random_text": random_text,
    "toml_ish_text": toml_ish_text,
    "keyvalue_lines": keyvalue_lines,
}