"""Generated strategy - iteration 4, attempt 1.
accepted: False
generated: 2026-08-14T05:52:08.050160+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.text(min_size=2, max_size=10).filter(lambda x: x.startswith('"') and x.endswith('"')),
        st.text(min_size=2, max_size=10).filter(lambda x: x.startswith("'") and x.endswith("'"))
    ))

@composite
def dotted_key(draw):
    return draw(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()) + 
                st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()))

@composite
def quoted_key(draw):
    return draw(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()).map(lambda x: f'"{x}"'))

@composite
def basic_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'))

@composite
def literal_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"))

@composite
def ml_basic_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}"""'))

@composite
def ml_literal_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"'''{x}'''"))

@composite
def escape_sequence(draw):
    return draw(st.text(min_size=1, max_size=1).map(lambda x: f"\\{x}"))

@composite
def unicode_escape(draw):
    return draw(st.text(min_size=4, max_size=4).map(lambda x: f"\\u{x}"))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        basic_string(),
        literal_string(),
        ml_basic_string(),
        ml_literal_string(),
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        escape_sequence(),
        unicode_escape(),
        st.integers(min_value=0, max_value=15).map(lambda x: f"0x{x}"),
        st.integers(min_value=0, max_value=7).map(lambda x: f"0o{x}"),
        st.integers(min_value=0, max_value=1).map(lambda x: f"0b{x}"),
        st.floats(min_value=-1e100, max_value=1e100).map(lambda x: f"{x:.20f}"),
        st.just("inf"),
        st.just("nan")
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(pair(), value()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"{{{', '.join(pairs)},}}"

@composite
def table(draw):
    return f"[{draw(key())}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table(), inline_table(), array()), min_size=0, max_size=10))
    return "\n".join(elements)

@composite
def nested_array(draw):
    elements = draw(st.lists(st.one_of(pair(), value(), array()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def nested_document(draw):
    elements = draw(st.lists(st.one_of(pair(), table(), inline_table(), array(), nested_array()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = st.recursive(
    st.one_of(pair(), table(), inline_table(), array(), nested_array()),
    lambda x: st.lists(x, min_size=0, max_size=10),
    max_leaves=20
)