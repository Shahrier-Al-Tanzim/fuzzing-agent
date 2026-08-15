"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-08-15T10:42:56.777504+00:00
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
    simple_keys = draw(st.lists(key(), min_size=2, max_size=5))
    return ".".join(simple_keys)

@composite
def escape_sequence(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=1).map(lambda x: f"\\{x}"),
        st.text(min_size=1, max_size=1).map(lambda x: f"\\u{x}"),
        st.text(min_size=1, max_size=1).map(lambda x: f"\\U{x}")
    ))

@composite
def unicode_escape(draw):
    return draw(st.one_of(
        st.text(min_size=4, max_size=4).map(lambda x: f"\\u{x}"),
        st.text(min_size=8, max_size=8).map(lambda x: f"\\U{x}")
    ))

@composite
def basic_string(draw):
    content = draw(st.text(min_size=0, max_size=10))
    return f'"{content}"'

@composite
def ml_basic_string(draw):
    content = draw(st.text(min_size=0, max_size=10))
    return f'"""{content}"""'

@composite
def literal_string(draw):
    content = draw(st.text(min_size=0, max_size=10))
    return f"'{content}'"

@composite
def ml_literal_string(draw):
    content = draw(st.text(min_size=0, max_size=10))
    return f"'''{content}'''"

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        basic_string(),
        ml_basic_string(),
        literal_string(),
        ml_literal_string(),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                  st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        array(),
        inline_table()
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    keyvals = draw(st.lists(st.tuples(key(), value()), min_size=0, max_size=10))
    return f"{{{', '.join(f'{k} = {v}' for k, v in keyvals)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()