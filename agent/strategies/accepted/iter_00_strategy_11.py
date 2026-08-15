"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-08-15T10:22:01.705821+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).filter(lambda x: all(c.isalnum() or c in '-_' for c in x))
    ))

@composite
def dotted_key(draw):
    keys = draw(st.lists(key(), min_size=1, max_size=5))
    return '.'.join(keys)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T00:00:00Z"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        array(),
        inline_table()
    ))

@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"{{{', '.join(pairs)}}}"

@composite
def table(draw):
    header = draw(st.one_of(key().map(lambda k: f"[{k}]"), key().map(lambda k: f"[[{k}]]")))
    return header

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()