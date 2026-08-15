"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-15T08:18:41.793255+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0{x}"),
        st.integers(min_value=2**63, max_value=10**20).map(str),
    ))

@composite
def float_(draw):
    return draw(st.one_of(
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"{x:.20f}"),
        st.just("inf"),
        st.just("-inf"),
        st.just("nan"),
    ))

@composite
def string(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=100).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=100).map(lambda x: f'"""{x}"""'),
        st.text(min_size=1, max_size=100).map(lambda x: f"'''{x}'''"),
    ))

@composite
def bool_(draw):
    return draw(st.sampled_from(["true", "false"]))

@composite
def datetime(draw):
    year = draw(st.integers(min_value=1970, max_value=2100))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"

@composite
def value(draw):
    return draw(st.one_of(
        integer(),
        float_(),
        string(),
        bool_(),
        datetime(),
    ))

@composite
def array(draw, max_depth=5, current_depth=0):
    if current_depth >= max_depth:
        elements = draw(st.lists(st.one_of(value(), string())))
    else:
        elements = draw(st.lists(st.one_of(value(), string(), array())))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw, max_depth=5, current_depth=0):
    if current_depth >= max_depth:
        pairs = draw(st.lists(st.tuples(string(), value())))
    else:
        pairs = draw(st.lists(st.tuples(string(), st.one_of(value(), array(), inline_table()))))
    return f"{{{', '.join(f'{key} = {value}' for key, value in pairs)}}}"

@composite
def pair(draw):
    key = draw(string())
    value_ = draw(st.one_of(value(), array(), inline_table()))
    return f"{key} = {value_}"

@composite
def table(draw):
    name = draw(string())
    return f"[{name}]"

@composite
def document(draw, max_size=100):
    elements = draw(st.lists(st.one_of(pair(), table()), max_size=max_size))
    return "\n".join(elements)

toml_strategy = document()