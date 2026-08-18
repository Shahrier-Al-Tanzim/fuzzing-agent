"""Generated strategy - iteration 4, attempt 1.
accepted: False
generated: 2026-08-16T13:35:40.604241+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()).map(lambda x: x)
    ))

@composite
def dotted_key(draw):
    parts = draw(st.lists(st.text(min_size=1, max_size=10), min_size=2))
    return ".".join(parts)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: 'true' if x else 'false')
    ))

@composite
def escape_sequence(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=1).map(lambda x: f"\\{x}"),
        st.text(min_size=1, max_size=1).map(lambda x: f"\\u{x}"),
        st.text(min_size=1, max_size=1).map(lambda x: f"\\U{x}"),
    ))

@composite
def unicode_escape(draw):
    return draw(st.one_of(
        st.text(min_size=4, max_size=4).map(lambda x: f"\\u{x}"),
        st.text(min_size=8, max_size=8).map(lambda x: f"\\U{x}"),
    ))

@composite
def ml_basic_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}"""'))

@composite
def ml_literal_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"'''{x}'''"))

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    elements = draw(st.lists(
        st.one_of(value(), array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1))
    ))
    return f"[{', '.join(elements)}]"

@composite
def array_shallow(draw):
    elements = draw(st.lists(
        st.one_of(value(), array(), array(), array(), array())
    ))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(
        st.tuples(key(), value())
    ))
    return f"{{{', '.join(f'{k} = {v}' for k, v in pairs)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(st.one_of(value(), array(), array_shallow(), inline_table(), ml_basic_string(), ml_literal_string(), unicode_escape(), st.integers(min_value=0, max_value=2**64-1).map(str), st.integers(min_value=-2**63-1, max_value=-1).map(str)))}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = st.one_of(
    document(),
    document(),
    document(),
    document(),
    document(),
    array(),
    array_shallow(),
    ml_basic_string(),
    ml_literal_string(),
    unicode_escape(),
    st.integers(min_value=0, max_value=2**64-1).map(str),
    st.integers(min_value=-2**63-1, max_value=-1).map(str),
    dotted_key()
)