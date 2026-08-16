"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-08-16T07:27:51.781603+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: all(c.isalnum() or c in '-_' for c in x)),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")
    ))

@composite
def dotted_key(draw):
    parts = draw(st.lists(key(), min_size=2))
    return ".".join(parts)

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
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59), st.integers(0, 999999))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:06d}"),
        array(),
        inline_table(),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '"'),
        st.text(min_size=1, max_size=10).map(lambda x: "'" + x + "'"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}\\n"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}\\n'"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}\\u000A"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}\\u000A'"),
        st.integers(min_value=0, max_value=9223372036854775807).map(str),
        st.integers(min_value=-9223372036854775808, max_value=-1).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}"""'),
        st.text(min_size=1, max_size=10).map(lambda x: "'''"+x+"'''"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}\\n"""'),
        st.text(min_size=1, max_size=10).map(lambda x: "'''"+x+"\\n'''"),
        st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}\\u000A"""'),
        st.text(min_size=1, max_size=10).map(lambda x: "'''"+x+"\\u000A'''"),
        st.integers(min_value=0, max_value=2**16-1).map(lambda x: f"0x{x:x}"),
        st.integers(min_value=0, max_value=2**8-1).map(lambda x: f"0o{x:o}"),
        st.integers(min_value=0, max_value=2**64-1).map(lambda x: f"0b{x:b}"),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"{x:.20f}"),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"inf" if x == float('inf') else f"-inf" if x == float('-inf') else f"nan" if x != x else f"{x:.20f}"),
    ))

@composite
def pair(draw):
    k = draw(st.one_of(key(), dotted_key()))
    v = draw(value())
    return f"{k} = {v}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0))
    return f"{{{', '.join(pairs)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0))
    return "\n".join(elements)

toml_strategy = document()