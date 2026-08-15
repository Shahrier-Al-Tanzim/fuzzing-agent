"""Generated strategy - iteration 0, attempt 6.
accepted: False
generated: 2026-08-15T09:24:59.468191+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=True, allow_infinity=True).map(str),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.dates(min_value=None, max_value=None).map(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S")),
        st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'),
        array(),
        inline_table()
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=100))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0, max_size=100))
    return f"{{{', '.join(pairs)}}}"

@composite
def pair(draw):
    key = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))
    value_str = draw(value())
    return f"{key} = {value_str}"

@composite
def table(draw):
    name = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))
    return f"[{name}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=100))
    return "\n".join(elements)

toml_strategy = document()