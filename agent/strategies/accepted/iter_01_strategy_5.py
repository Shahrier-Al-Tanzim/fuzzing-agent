"""Generated strategy - iteration 1, attempt 2.
accepted: True
generated: 2026-08-15T10:30:23.126671+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).map(lambda x: x)))

@composite
def dotted_key(draw):
    keys = draw(st.lists(key(), min_size=2))
    return ".".join(keys)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}")))

@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def array(draw, max_depth=5, current_depth=0):
    if current_depth >= max_depth:
        elements = draw(st.lists(value(), min_size=0, max_size=10))
    else:
        elements = draw(st.lists(st.one_of(value(), array(max_depth=max_depth, current_depth=current_depth+1)), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw, max_depth=5, current_depth=0):
    if current_depth >= max_depth:
        elements = draw(st.lists(pair(), min_size=0, max_size=10))
    else:
        elements = draw(st.lists(st.one_of(pair(), array(max_depth=max_depth, current_depth=current_depth+1)), min_size=0, max_size=10))
    return f"{{{', '.join(elements)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()