"""Generated strategy - iteration 0, attempt 7.
accepted: False
generated: 2026-08-14T08:54:43.953251+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def simple_key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'),
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda x: f"'{x}'")
    ))

@composite
def dotted_key(draw):
    keys = [draw(simple_key()) for _ in range(2)]
    return '.'.join(keys)

@composite
def key(draw):
    return draw(st.one_of(simple_key(), dotted_key()))

@composite
def string(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-').map(lambda x: f"'{x}'")
    ))

@composite
def integer(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000, max_value=1000).map(str),
        st.text(min_size=1, max_size=20, alphabet='0123456789').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789').map(lambda x: f'-{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789').map(lambda x: f'0x{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789').map(lambda x: f'0o{x}'),
        st.text(min_size=1, max_size=20, alphabet='01').map(lambda x: f'0b{x}')
    ))

@composite
def floating_point(draw):
    return draw(st.one_of(
        st.floats(min_value=-1000, max_value=1000).map(str),
        st.text(min_size=1, max_size=20, alphabet='0123456789.').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789.e').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789.E').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789.').map(lambda x: f'-{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789.e').map(lambda x: f'-{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789.E').map(lambda x: f'-{x}')
    ))

@composite
def bool_(draw):
    return draw(st.one_of(st.just('true'), st.just('false')))

@composite
def date_time(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=20, alphabet='0123456789-:').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789-:Z').map(lambda x: f'{x}'),
        st.text(min_size=1, max_size=20, alphabet='0123456789-:+').map(lambda x: f'{x}')
    ))

@composite
def value(draw):
    return draw(st.one_of(string(), integer(), floating_point(), bool_(), date_time()))

@composite
def key_value(draw):
    k = draw(key())
    v = draw(value())
    return f'{k} = {v}'

@composite
def array(draw):
    values = [draw(value()) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return f'[{", ".join(values)}]'

@composite
def inline_table(draw):
    key_values = [draw(key_value()) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return f'{{{", ".join(key_values)}}}'

@composite
def table(draw):
    return draw(st.one_of(array(), inline_table()))

@composite
def document(draw):
    expressions = [draw(st.one_of(key_value(), table())) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return '\n'.join(expressions)

toml_strategy = document()