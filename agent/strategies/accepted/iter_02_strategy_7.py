"""Generated strategy - iteration 2, attempt 2.
accepted: True
generated: 2026-08-15T10:54:41.052316+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")
    ))

@composite
def dotted_key(draw):
    return draw(st.lists(key(), min_size=2, max_size=5)).map(lambda parts: ".".join(parts))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=False).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                  st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.text(min_size=2, max_size=10).map(lambda x: f'"{x}"' + '"'),
        st.text(min_size=2, max_size=10).map(lambda x: f"'" + x + "'"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}\\u0000"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}\\u0000'"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}\\n"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}\\n'")
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table())))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    elements = draw(st.lists(st.tuples(key(), value())))
    return f"{{{', '.join(f'{k} = {v}' for k, v in elements)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = document()