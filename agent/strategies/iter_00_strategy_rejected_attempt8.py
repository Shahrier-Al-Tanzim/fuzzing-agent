"""Generated strategy - iteration 0, attempt 8.
accepted: False
generated: 2026-09-02T21:22:13.699334+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STRING_CHARS = st.text(min_size=1, max_size=100).filter(lambda x: '"' not in x and '\\' not in x and '\n' not in x)
LITERAL_STRING_CHARS = st.text(min_size=1, max_size=100).filter(lambda x: "'" not in x and '\n' not in x)

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=20),
        BASIC_STRING_CHARS.map(lambda s: f'"{s}"'),
        LITERAL_STRING_CHARS.map(lambda s: f"'{s}'")
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers().map(str),
        st.floats().map(str),
        st.just('true'),
        st.just('false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        array(),
        inline_table(),
        BASIC_STRING_CHARS.map(lambda s: f'"{s}"'),
        LITERAL_STRING_CHARS.map(lambda s: f"'{s}'")
    ))

@composite
def inline_table(draw):
    keyvals = draw(st.lists(st.tuples(key(), value()), min_size=1, max_size=10))
    return "{" + ", ".join(f"{k}={v}" for k, v in keyvals) + "}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array()), min_size=0, max_size=10))
    return "[" + ", ".join(elements) + "]"

@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

@composite
def table(draw):
    tbl_key = draw(key())
    return f"[{tbl_key}]"

def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[table]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    document(),
    many_siblings()
)