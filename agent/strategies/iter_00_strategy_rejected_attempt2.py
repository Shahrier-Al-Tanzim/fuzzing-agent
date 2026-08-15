"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-08-15T09:23:00.711893+00:00
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
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        array(),
        inline_table()
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=100))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    keyvals = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'), value()), min_size=0, max_size=100))
    return f"{{{', '.join(f'{key} = {value}' for key, value in keyvals)}}}"

@composite
def table(draw):
    return f"[{draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))}]"

@composite
def pair(draw):
    return f"{draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))} = {draw(value())}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=100))
    return "\n".join(elements)

toml_strategy = document()