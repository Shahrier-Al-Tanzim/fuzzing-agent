"""Generated strategy - iteration 0, attempt 3.
accepted: True
generated: 2026-08-13T07:25:56.513984+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(min_size=1, max_size=100),
        st.sampled_from(["true", "false"]),
        st.sampled_from(["inf", "-inf", "nan"]),
    ))

@composite
def array_value(draw):
    elements = draw(st.lists(scalar_value() | array_value() | inline_table_value(), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table_key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=100),
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
    ))

@composite
def inline_table_value(draw):
    pairs = draw(st.lists(st.tuples(inline_table_key(), scalar_value() | array_value() | inline_table_value()), min_size=0, max_size=10))
    return "{" + ", ".join(f"{key} = {value}" for key, value in pairs) + "}"

@composite
def table_value(draw):
    key = draw(inline_table_key())
    value = draw(scalar_value() | array_value() | inline_table_value())
    return f"{key} = {value}"

@composite
def document(draw):
    statements = draw(st.lists(table_value(), min_size=0, max_size=10))
    return "\n".join(statements)

toml_strategy = document()