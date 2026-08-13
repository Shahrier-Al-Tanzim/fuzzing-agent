"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-08-13T08:31:38.796183+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return draw(st.integers(min_value=-2**63, max_value=2**63-1))

@composite
def float_(draw):
    return draw(st.floats(min_value=-1e100, max_value=1e100))

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
    elements = draw(st.lists(value(), min_size=0, max_size=100))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(key_value(), min_size=0, max_size=100))
    return f"{{{', '.join(pairs)}}}"

@composite
def table(draw):
    return draw(st.one_of(array(), inline_table()))

@composite
def document(draw):
    elements = draw(st.lists(key_value(), min_size=0, max_size=100))
    return '\n'.join(elements)

toml_strategy = document()