"""Generated strategy - iteration 0, attempt 6.
accepted: False
generated: 2026-08-14T08:54:16.722152+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return str(draw(st.integers(min_value=-2**63, max_value=2**63-1)))

@composite
def float_(draw):
    return str(draw(st.floats(min_value=-1e100, max_value=1e100)))

@composite
def string(draw):
    return draw(st.text(max_size=100))

@composite
def key(draw):
    return draw(st.text(max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'))

@composite
def value(draw):
    return draw(st.one_of(integer(), float_(), string()))

@composite
def key_value(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw):
    elements = draw(st.lists(value(), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    key_values = draw(st.lists(key_value(), min_size=0, max_size=10))
    return f"{{{', '.join(key_values)}}}"

@composite
def table(draw):
    return draw(st.one_of(array(), inline_table()))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(key_value(), table()), min_size=0, max_size=10))
    return '\n'.join(elements)

toml_strategy = document()