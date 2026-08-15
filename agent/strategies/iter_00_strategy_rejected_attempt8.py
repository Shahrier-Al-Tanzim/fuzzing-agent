"""Generated strategy - iteration 0, attempt 8.
accepted: False
generated: 2026-08-15T08:05:05.600860+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers().map(str),
        st.floats().map(str),
        st.text().map(lambda x: f'"{x}"'),
        st.booleans().map(str),
        st.none().map(lambda x: 'null')
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.recursive(value(), lambda x: st.one_of(x, array(), inline_table()), max_leaves=100)))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(st.tuples(st.text(), value())))
    return "{" + ", ".join(f"{k} = {v}" for k, v in pairs) + "}"

@composite
def table(draw):
    name = draw(st.text())
    return f"[{name}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table(), table())))
    return "\n".join(elements)

toml_strategy = document()