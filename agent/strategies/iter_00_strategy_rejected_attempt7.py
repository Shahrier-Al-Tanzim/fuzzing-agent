"""Generated strategy - iteration 0, attempt 7.
accepted: False
generated: 2026-08-15T09:25:28.533442+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0{x}"),
    ))

@composite
def float_(draw):
    return draw(st.one_of(
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=False),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=False).map(lambda x: f"{x:.20f}"),
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
def boolean(draw):
    return draw(st.booleans())

@composite
def datetime(draw):
    return draw(st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    )).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}-07:00")

@composite
def value(draw):
    return draw(st.one_of(
        integer(),
        float_(),
        string(),
        boolean(),
        datetime(),
    ))

@composite
def array(draw, elements=value()):
    return draw(st.lists(elements)).map(lambda x: f"[{', '.join(map(str, x))}]")

@composite
def inline_table(draw, elements=value()):
    return draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), elements))).map(
        lambda x: f"{{{', '.join(f'{k} = {v}' for k, v in x)}}}"
    )

@composite
def table(draw):
    return draw(st.text(min_size=1, max_size=100)).map(lambda x: f"[{x}]")

@composite
def pair(draw):
    return draw(st.tuples(
        st.text(min_size=1, max_size=100),
        st.one_of(value(), array(), inline_table()),
    )).map(lambda x: f"{x[0]} = {x[1]}")

@composite
def document(draw):
    return draw(st.lists(st.one_of(pair(), table()))).map(lambda x: "\n".join(map(str, x)))

toml_strategy = document()