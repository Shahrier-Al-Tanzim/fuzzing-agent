"""Generated strategy - iteration 1, attempt 1.
accepted: False
generated: 2026-08-15T09:33:08.195794+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")
    ))

@composite
def unquoted_key(draw):
    return draw(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()))

@composite
def dotted_key(draw):
    return draw(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()) + 
                 st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()))

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
        )
    ))

@composite
def ml_basic_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}"""'))

@composite
def ml_literal_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"'''{x}'''"))

@composite
def pair(draw):
    k = draw(st.one_of(key(), unquoted_key(), dotted_key()))
    v = draw(st.one_of(value(), ml_basic_string(), ml_literal_string()))
    return f"{k} = {v}"

@composite
def table(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f"[{x}]"),
        st.text(min_size=1, max_size=10).map(lambda x: f"[[{x}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = document()