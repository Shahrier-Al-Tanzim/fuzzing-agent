"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-13T08:40:57.892219+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=1, max_size=10),
        st.text(alphabet='"', min_size=1, max_size=1) + st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=0, max_size=9) + st.text(alphabet='"', min_size=1, max_size=1),
        st.text(alphabet="'", min_size=1, max_size=1) + st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=0, max_size=9) + st.text(alphabet="'", min_size=1, max_size=1)
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=True, allow_infinity=True).map(str),
        st.text(alphabet='"', min_size=1, max_size=1) + st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=0, max_size=100) + st.text(alphabet='"', min_size=1, max_size=1),
        st.text(alphabet="'", min_size=1, max_size=1) + st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', min_size=0, max_size=100) + st.text(alphabet="'", min_size=1, max_size=1),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.dates(min_value='1970-01-01', max_value='2100-12-31').map(lambda x: x.isoformat()),
        st.datetimes(min_value='1970-01-01 00:00:00', max_value='2100-12-31 23:59:59').map(lambda x: x.isoformat())
    ))

@composite
def array(draw):
    return '[' + ', '.join(draw(st.lists(value(), min_size=0, max_size=10))) + ']'

@composite
def inline_table(draw):
    return '{' + ', '.join(draw(st.lists(st.tuples(key(), value()), min_size=0, max_size=10))).map(lambda pairs: ', '.join(f'{k} = {v}' for k, v in pairs)) + '}'

@composite
def table(draw):
    return '[' + draw(key()) + ']' + '\n' + draw(st.one_of(array(), inline_table()))

@composite
def document(draw):
    return '\n'.join(draw(st.lists(st.one_of(st.tuples(key(), value()), table()), min_size=0, max_size=10))).map(lambda elements: '\n'.join(f'{k} = {v}' if isinstance(k, str) else k for k, v in elements))

toml_strategy = document()