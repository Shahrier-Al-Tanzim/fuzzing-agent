"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-08-14T08:53:25.798960+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0{x}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"{x}_"),
    ))

@composite
def float_(draw):
    return draw(st.one_of(
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"{x}e10"),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"{x}e-10"),
    ))

@composite
def string(draw):
    return draw(st.one_of(
        st.text(),
        st.text().map(lambda x: f'"{x}"'),
        st.text().map(lambda x: f"'{x}'"),
    ))

@composite
def key(draw):
    return draw(st.one_of(
        st.text(),
        st.text().map(lambda x: f'"{x}"'),
        st.text().map(lambda x: f"'{x}'"),
    ))

@composite
def value(draw):
    return draw(st.one_of(
        integer(),
        float_(),
        string(),
        st.booleans().map(lambda x: "true" if x else "false"),
    ))

@composite
def pair(draw):
    return draw(st.tuples(key(), value())).map(lambda x: f"{x[0]} = {x[1]}")

@composite
def array(draw, elements=st.lists(value(), min_size=0, max_size=10)):
    return draw(elements).map(lambda x: f"[{', '.join(x)}]")

@composite
def inline_table(draw, elements=st.lists(pair(), min_size=0, max_size=10)):
    return draw(elements).map(lambda x: f"{{{', '.join(x)}}}")

@composite
def table(draw, elements=st.lists(pair(), min_size=0, max_size=10)):
    return draw(elements).map(lambda x: f"[{', '.join(x)}]")

@composite
def document(draw):
    return draw(st.lists(st.one_of(pair(), array(), inline_table(), table()), min_size=0, max_size=10)).map(lambda x: "\n".join(x))

toml_strategy = document()