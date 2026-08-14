"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-08-13T12:00:10.444478+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Define a strategy for generating keys
@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=1, max_size=100),
        st.text(alphabet='\'\'\'', min_size=1, max_size=100).map(lambda x: x + draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=1, max_size=100)) + x)
    ))

# Define a strategy for generating scalar values
@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000000000, max_value=1000000000).map(str),
        st.floats(min_value=-1000000000.0, max_value=1000000000.0, allow_nan=False, allow_infinity=False).map(str),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=1, max_size=100),
        st.text(alphabet='\'\'\'', min_size=1, max_size=100).map(lambda x: x + draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=1, max_size=100)) + x)
    ))

# Define a strategy for generating arrays
@composite
def array(draw):
    values = draw(st.lists(scalar_value() | array() | inline_table(), min_size=0, max_size=10))
    return '[' + ', '.join(values) + ']'

# Define a strategy for generating inline tables
@composite
def inline_table(draw):
    pairs = draw(st.lists(st.tuples(key(), scalar_value() | array() | inline_table()), min_size=0, max_size=10))
    return '{ ' + ', '.join(f'{k} = {v}' for k, v in pairs) + ' }'

# Define a strategy for generating tables
@composite
def table(draw):
    pairs = draw(st.lists(st.tuples(key(), scalar_value() | array() | inline_table()), min_size=0, max_size=10))
    return '[ ' + ', '.join(f'{k} = {v}' for k, v in pairs) + ' ]'

# Define a strategy for generating documents
@composite
def document(draw):
    elements = draw(st.lists(key_value() | table() | inline_table(), min_size=0, max_size=10))
    return '\n'.join(elements)

# Define a strategy for generating key-value pairs
@composite
def key_value(draw):
    return f'{draw(key())} = {draw(scalar_value() | array() | inline_table())}'

toml_strategy = document()