"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-14T08:52:45.446055+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def int_strategy(draw):
    return draw(st.integers(min_value=-2**63, max_value=2**63-1))

@composite
def float_strategy(draw):
    return draw(st.floats(min_value=-1e308, max_value=1e308, allow_nan=True, allow_infinity=True))

@composite
def string_strategy(draw):
    return draw(st.text(min_size=1, max_size=100))

@composite
def key_strategy(draw):
    return draw(st.one_of(string_strategy(), int_strategy().map(str)))

@composite
def value_strategy(draw):
    return draw(st.one_of(string_strategy(), int_strategy(), float_strategy()))

@composite
def pair_strategy(draw):
    key = draw(key_strategy())
    value = draw(value_strategy())
    return (key, value)

@composite
def array_strategy(draw, max_size=10):
    size = draw(st.integers(min_value=0, max_value=max_size))
    return draw(st.lists(value_strategy(), min_size=size, max_size=size))

@composite
def table_strategy(draw, max_size=10):
    size = draw(st.integers(min_value=0, max_value=max_size))
    return draw(st.lists(pair_strategy(), min_size=size, max_size=size))

@composite
def document_strategy(draw, max_size=10):
    size = draw(st.integers(min_value=0, max_value=max_size))
    tables = draw(st.lists(table_strategy(), min_size=size, max_size=size))
    return "\n".join([f"[{table[0][0]}]\n" + "\n".join([f"{key} = {value}" for key, value in table]) for table in tables])

toml_strategy = document_strategy()