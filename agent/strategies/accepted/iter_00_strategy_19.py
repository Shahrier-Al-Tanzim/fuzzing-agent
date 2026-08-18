"""Generated strategy - iteration 0, attempt 5.
accepted: True
generated: 2026-08-16T17:49:46.588598+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
UNQUOTED_KEY = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
QUOTED_KEY = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"')
KEY = st.one_of(UNQUOTED_KEY, QUOTED_KEY)

VALUE = st.one_of(
    st.integers(min_value=-2**63, max_value=2**63-1).map(str),
    st.floats(min_value=-1e10, max_value=1e10).map(str),
    st.booleans().map(lambda x: "true" if x else "false"),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
)

@composite
def pair(draw):
    k = draw(KEY)
    v = draw(VALUE)
    return f"{k} = {v}"

@composite
def table(draw):
    name = draw(KEY)
    return f"[{name}]"

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(st.one_of(VALUE, array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1))))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(st.one_of(pair(), inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1))))
    return f"{{{', '.join(elements)}}}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = document()