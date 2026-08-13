"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-08-13T08:41:00.734703+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers().map(str),
        st.floats().map(str),
        st.text(),
        st.sampled_from(["true", "false"]),
        st.sampled_from(["inf", "-inf", "nan"]),
    ))

@composite
def array_value(draw):
    return "[" + ", ".join(draw(st.lists(scalar_value(), min_size=1, max_size=10))) + "]"

@composite
def inline_table_value(draw):
    pairs = draw(st.lists(st.tuples(st.text(), scalar_value()), min_size=1, max_size=10))
    return "{" + ", ".join(f"{key} = {value}" for key, value in pairs) + "}"

@composite
def table_value(draw):
    return draw(st.one_of(
        st.text().map(lambda x: f"[{x}]"),
        array_value(),
        inline_table_value(),
    ))

@composite
def key_value_pair(draw):
    key = draw(st.text())
    value = draw(table_value())
    return f"{key} = {value}"

@composite
def toml_document(draw):
    pairs = draw(st.lists(key_value_pair(), min_size=1, max_size=10))
    return "\n".join(pairs)

toml_strategy = toml_document()