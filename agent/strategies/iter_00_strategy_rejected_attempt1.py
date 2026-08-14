"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-13T11:58:59.197479+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def simple_key(draw):
    return draw(st.one_of(st.text(min_size=1, max_size=10).filter(lambda x: x.isalnum() and x[0].isalpha()),
                           st.text(min_size=2, max_size=10).filter(lambda x: x[0] == '"' and x[-1] == '"'),
                           st.text(min_size=2, max_size=10).filter(lambda x: x[0] == "'" and x[-1] == "'")))

@composite
def dotted_key(draw):
    return draw(st.lists(simple_key(), min_size=2, max_size=5)).map(lambda x: ".".join(x))

@composite
def key(draw):
    return draw(st.one_of(simple_key(), dotted_key()))

@composite
def string(draw):
    return draw(st.one_of(st.text(min_size=1, max_size=10).filter(lambda x: x[0] == '"' and x[-1] == '"'),
                           st.text(min_size=1, max_size=10).filter(lambda x: x[0] == "'" and x[-1] == "'")))

@composite
def integer(draw):
    return draw(st.one_of(st.integers(min_value=-2**63, max_value=2**63-1).map(str),
                           st.text(min_size=1, max_size=10).filter(lambda x: x[0] == '0' and x[1:].isdigit())))

@composite
def floating_point(draw):
    return draw(st.one_of(st.floats(min_value=-1e10, max_value=1e10).map(str),
                           st.text(min_size=1, max_size=10).filter(lambda x: '.' in x)))

@composite
def bool_(draw):
    return draw(st.sampled_from(['true', 'false']))

@composite
def date_time(draw):
    return draw(st.text(min_size=1, max_size=20).filter(lambda x: '-' in x and ':' in x))

@composite
def value(draw):
    return draw(st.one_of(string(), integer(), floating_point(), bool_(), date_time()))

@composite
def key_value(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def array_values(draw):
    return draw(st.lists(value(), min_size=0, max_size=5)).map(lambda x: ", ".join(x))

@composite
def array_(draw):
    return draw(st.one_of(st.just("[]"), st.text(min_size=1, max_size=10).filter(lambda x: x[0] == '[' and x[-1] == ']')))

@composite
def inline_table_keyvals(draw):
    return draw(st.lists(st.tuples(key(), value()), min_size=0, max_size=5)).map(lambda x: ", ".join(f"{k} = {v}" for k, v in x))

@composite
def inline_table(draw):
    return draw(st.one_of(st.just("{}"), st.text(min_size=1, max_size=10).filter(lambda x: x[0] == '{' and x[-1] == '}')))

@composite
def table(draw):
    return draw(st.one_of(st.just("[]"), st.text(min_size=1, max_size=10).filter(lambda x: x[0] == '[' and x[-1] == ']')))

@composite
def expression(draw):
    return draw(st.one_of(key_value(), table(), inline_table()))

@composite
def document(draw):
    return draw(st.lists(expression(), min_size=0, max_size=5)).map(lambda x: "\n".join(x))

toml_strategy = document()