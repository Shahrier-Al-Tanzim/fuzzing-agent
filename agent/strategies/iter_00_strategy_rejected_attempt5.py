"""Generated strategy - iteration 0, attempt 5.
accepted: False
generated: 2026-08-14T08:53:49.805579+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def int_value(draw):
    return draw(st.integers(min_value=-2**63, max_value=2**63-1)).map(str)

@composite
def float_value(draw):
    return draw(st.floats(min_value=-1e100, max_value=1e100)).map(str)

@composite
def bool_value(draw):
    return draw(st.sampled_from(["true", "false"]))

@composite
def string_value(draw):
    return draw(st.text(min_size=1, max_size=100))

@composite
def date_time_value(draw):
    year = draw(st.integers(min_value=1970, max_value=2100))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"

@composite
def array_value(draw):
    values = draw(st.lists(st.one_of(int_value(), float_value(), bool_value(), string_value(), date_time_value()), min_size=0, max_size=10))
    return "[" + ", ".join(values) + "]"

@composite
def table_value(draw):
    pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), st.one_of(int_value(), float_value(), bool_value(), string_value(), date_time_value(), array_value())), min_size=0, max_size=10))
    return "{" + ", ".join(f"{key} = {value}" for key, value in pairs) + "}"

@composite
def document_value(draw):
    expressions = draw(st.lists(st.one_of(table_value(), array_value(), st.tuples(st.text(min_size=1, max_size=100), st.one_of(int_value(), float_value(), bool_value(), string_value(), date_time_value(), array_value()))), min_size=0, max_size=10))
    return "\n".join(f"{key} = {value}" if isinstance(value, str) else f"{value}" for key, value in expressions if isinstance(value, str) or (isinstance(value, tuple) and isinstance(value[1], str)))

toml_strategy = document_value()