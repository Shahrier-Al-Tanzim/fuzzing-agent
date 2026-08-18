"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-08-17T03:08:24.442565+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

import string

UNQUOTED_KEY_CHARS = string.ascii_letters + string.digits + "-_"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        st.text(alphabet=string.printable.replace('"', '').replace("\\", "")
                 .replace("\n", "").replace("\r", ""),
                 min_size=1, max_size=10).map(lambda x: f'"{x}"')
    ))

@composite
def dotted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
                + st.lists(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
                            .map(lambda x: "." + x)))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(alphabet=string.printable.replace('"', '').replace("\\", "")
                 .replace("\n", "").replace("\r", ""),
                 min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                   st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.lists(st.one_of(value(), array(), inline_table())).map(lambda x: f"[{', '.join(x)}]"),
        st.lists(st.one_of(key(), value())).map(lambda x: f"{{{', '.join(x)}}}")
    ))

@composite
def array(draw):
    elements = draw(st.lists(
        st.one_of(value(), array(), inline_table())
    ))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    elements = draw(st.lists(
        st.tuples(key(), value()).map(lambda x: f"{x[0]}={x[1]}")
    ))
    return f"{{{', '.join(elements)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def pair(draw):
    return draw(st.tuples(key(), value()).map(lambda x: f"{x[0]}={x[1]}"))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return f"a = {[\"1\"] * n}"

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return f"a = {{{', '.join([f'b{i} = 1' for i in range(n)])}}}"

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return f"a.{'.a' * n} = 1"

toml_strategy = st.one_of(document(), document(), deep_array(), deep_inline_table(), deep_dotted_key())