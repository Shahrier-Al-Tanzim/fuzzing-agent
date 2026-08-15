"""Generated strategy - iteration 1, attempt 2.
accepted: False
generated: 2026-08-15T09:29:23.437873+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=100).map(lambda x: f"'{x}'"),
        array(),
        inline_table(),
        unquoted_key_value(),
        dotted_key_value(),
        ml_basic_string_value(),
        ml_literal_string_value(),
        escape_sequence_value()
    ))

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(map(str, elements))}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"{{{', '.join(map(str, pairs))}}}"

@composite
def pair(draw):
    key = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))
    val = draw(value())
    return f"{key} = {val}"

@composite
def table(draw):
    name = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))
    pairs = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"[{name}]\n" + "\n".join(pairs)

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

@composite
def unquoted_key_value(draw):
    key = draw(st.text(min_size=1, max_size=100).map(lambda x: x.replace('.', '_')))
    val = draw(value())
    return f"{key} = {val}"

@composite
def dotted_key_value(draw):
    key = draw(st.text(min_size=1, max_size=100).map(lambda x: x.replace('.', '.')))
    val = draw(value())
    return f"{key} = {val}"

@composite
def ml_basic_string_value(draw):
    val = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"""{x}"""'))
    return val

@composite
def ml_literal_string_value(draw):
    val = draw(st.text(min_size=1, max_size=100).map(lambda x: f"'''{x}'''"))
    return val

@composite
def escape_sequence_value(draw):
    val = draw(st.text(min_size=1, max_size=100).map(lambda x: f'"{x}"'))
    return val.replace('\\', '\\\\').replace('"', '\\"')

toml_strategy = document()