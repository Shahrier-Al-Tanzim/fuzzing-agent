"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-08-15T09:34:23.983060+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Define a strategy for generating keys
@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")
    ))

# Define a strategy for generating values
@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.recursive(
            st.one_of(st.integers(min_value=-2**63, max_value=2**63-1).map(str),
                       st.floats(min_value=-1e10, max_value=1e10).map(str),
                       st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
                       st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")),
            lambda x: st.lists(x).map(lambda y: f"[{', '.join(y)}]"),
            max_leaves=100
        ),
        st.recursive(
            st.one_of(key(), value()),
            lambda x: st.lists(st.tuples(key(), x)).map(lambda y: f"{{{', '.join(f'{k} = {v}' for k, v in y)}}}"),
            max_leaves=100
        ),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"').map(lambda x: x.replace('"', '\\"')),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'").map(lambda x: x.replace("'", "\\'")),
        st.integers(min_value=0, max_value=2**63-1).map(lambda x: f"0{x}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"{x}.9999999999999999999"),
        st.integers(min_value=2**63, max_value=2**64-1).map(str)
    ))

# Define a strategy for generating pairs
@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

# Define a strategy for generating tables
@composite
def table(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f"[{x}]"),
        st.text(min_size=1, max_size=10).map(lambda x: f"[[{x}]]")
    ))

# Define a strategy for generating documents
@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = document()