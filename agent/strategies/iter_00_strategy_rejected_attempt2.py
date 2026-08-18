"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-08-17T03:06:48.136224+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-", min_size=1, max_size=10).map(lambda x: f'"{x}"')
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.dates(min_value=None, max_value=None).map(lambda x: x.isoformat()),
        st.times(min_value=None, max_value=None).map(lambda x: x.isoformat()),
        array(),
        inline_table()
    ))

@composite
def array(draw):
    elements = draw(st.lists(
        st.one_of(value(), array(), array(), array(), array())
    ))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(
        st.tuples(key(), value())
    ))
    return "{" + ", ".join(f"{k} = {v}" for k, v in pairs) + "}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def document(draw):
    elements = draw(st.lists(
        st.one_of(pair(), table())
    ))
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

toml_strategy = st.one_of(document(), document(), deep_array().map(lambda x: f"deep = {x}"), deep_inline_table().map(lambda x: f"deep = {x}"), deep_dotted_key().map(lambda x: f"{x} = 1"))