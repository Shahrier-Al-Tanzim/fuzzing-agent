"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-08-15T09:24:02.661607+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100).map(str),
        st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T00:00:00Z"),
        array(),
        inline_table()
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=100))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    keyvals = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), value()), min_size=0, max_size=100))
    return f"{{{', '.join(f'{key} = {value}' for key, value in keyvals)}}}"

@composite
def pair(draw):
    key = draw(st.text(min_size=1, max_size=100))
    value_ = draw(value())
    return f"{key} = {value_}"

@composite
def table(draw):
    name = draw(st.text(min_size=1, max_size=100))
    return f"[{name}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=100))
    return "\n".join(elements)

toml_strategy = document()