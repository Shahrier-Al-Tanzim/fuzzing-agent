"""Generated strategy - iteration 0, attempt 3.
accepted: False
generated: 2026-08-15T09:23:26.787638+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=True, allow_infinity=True).map(str),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=100).map(lambda x: f"'{x}'"),
        array(),
        inline_table()
    ))

@composite
def pair(draw):
    key = draw(st.text(min_size=1, max_size=100))
    val = draw(value())
    return f"{key} = {val}"

@composite
def table(draw):
    name = draw(st.text(min_size=1, max_size=100))
    elements = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"[{name}]\n" + "\n".join(elements)

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    elements = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"{{{', '.join(elements)}}}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()