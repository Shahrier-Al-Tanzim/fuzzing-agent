"""Generated strategy - iteration 0, attempt 8.
accepted: False
generated: 2026-08-14T08:55:11.499912+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Define a strategy for generating keys
@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'),
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda s: f'"{s}"'),
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda s: f"'{s}'")
    ))

# Define a strategy for generating scalar values
@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-100, max_value=100).map(str),
        st.floats(min_value=-100, max_value=100).map(str),
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda s: f'"{s}"'),
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda s: f"'{s}'"),
        st.sampled_from(['true', 'false']),
        st.sampled_from(['inf', '-inf', 'nan'])
    ))

# Define a strategy for generating arrays
@composite
def array(draw, elements):
    return draw(st.lists(elements, min_size=0, max_size=10)).map(lambda lst: '[' + ', '.join(lst) + ']')

# Define a strategy for generating inline tables
@composite
def inline_table(draw):
    pairs = draw(st.lists(st.tuples(key(), scalar_value()), min_size=0, max_size=10))
    return draw(st.one_of(
        st.just('{}'),
        st.just('{ ' + ', '.join(f'{k} = {v}' for k, v in pairs) + ' }')
    ))

# Define a strategy for generating tables
@composite
def table(draw):
    return draw(st.one_of(
        st.just('[]'),
        st.just('[ ' + ', '.join(scalar_value() for _ in range(10)) + ' ]')
    ))

# Define a strategy for generating documents
@composite
def document(draw):
    return draw(st.one_of(
        st.just(''),
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'),
        key().map(lambda k: f'{k} = {scalar_value()}'),
        inline_table(),
        table()
    ))

toml_strategy = document()