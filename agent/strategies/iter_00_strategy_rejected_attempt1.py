"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-17T03:06:19.572576+00:00
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
                 .map(lambda x: x) | key().map(lambda k: k))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(alphabet=string.printable.replace('"', '').replace("\\", "")
                 .replace("\n", "").replace("\r", ""),
                 min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=3, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                   st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.one_of(st.integers(min_value=-2**63, max_value=2**63-1).map(str),
                  st.floats(min_value=-1e100, max_value=1e100).map(str),
                  st.text(alphabet=string.printable.replace('"', '').replace("\\", "")
                           .replace("\n", "").replace("\r", ""),
                           min_size=1, max_size=10).map(lambda x: f'"{x}"'),
                  st.text(min_size=3, max_size=10).map(lambda x: f"'{x}'"),
                  st.booleans().map(lambda x: "true" if x else "false"),
                  st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                           st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
                      .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
                  st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
                      .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
                  st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
                      .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
                  array(),
                  inline_table()
                 )
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), array(), array(), array())))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    elements = draw(st.lists(st.one_of(value(), array(), array(), array(), array())))
    return f"{{{', '.join(elements)}}}"

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def table(draw):
    return f"[{draw(key())}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "a." * n + "k"

toml_strategy = st.one_of(document(), document(), document(),
                          f"deep = {deep_array()}", f"deep = {deep_inline_table()}", f"deep = {deep_dotted_key()}")