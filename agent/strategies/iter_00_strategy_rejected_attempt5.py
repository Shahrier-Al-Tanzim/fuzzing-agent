"""Generated strategy - iteration 0, attempt 5.
accepted: False
generated: 2026-08-15T09:24:31.450561+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers().map(str),
        st.floats().map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        array(),
        inline_table()
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=10), value()), min_size=0, max_size=10))
    return f"{{{', '.join(f'{key} = {value}' for key, value in pairs)}}}"

@composite
def pair(draw):
    key = draw(st.text(min_size=1, max_size=10))
    value_ = draw(value())
    return f"{key} = {value_}"

@composite
def table(draw):
    name = draw(st.text(min_size=1, max_size=10))
    return f"[{name}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()