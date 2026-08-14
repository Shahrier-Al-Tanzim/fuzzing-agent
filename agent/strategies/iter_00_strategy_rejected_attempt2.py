"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-08-13T11:53:37.641560+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def integer(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.integers(min_value=2**63, max_value=10**20).map(str),
        st.integers(min_value=-10**20, max_value=-2**63-1).map(str)
    ))

@composite
def float_(draw):
    return draw(st.one_of(
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=False, allow_infinity=False).map(str),
        st.just("inf"),
        st.just("-inf"),
        st.just("nan")
    ))

@composite
def string(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100).map(lambda s: f'"{s}"'),
        st.text(min_size=1, max_size=100).map(lambda s: f"'{s}'")
    ))

@composite
def boolean(draw):
    return draw(st.booleans()).map(lambda b: "true" if b else "false")

@composite
def datetime(draw):
    return draw(st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59)
    )).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}")

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(integer(), float_(), string(), boolean(), datetime()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    key_value_pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=10), st.one_of(integer(), float_(), string(), boolean(), datetime())), min_size=0, max_size=10))
    return f"{{{', '.join(f'{k} = {v}' for k, v in key_value_pairs)}}}"

@composite
def table(draw):
    key_value_pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=10), st.one_of(integer(), float_(), string(), boolean(), datetime(), array(), inline_table())), min_size=0, max_size=10))
    return "\n".join(f"{k} = {v}" for k, v in key_value_pairs)

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(integer(), float_(), string(), boolean(), datetime(), array(), inline_table(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()