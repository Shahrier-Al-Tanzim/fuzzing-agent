"""Generated strategy - iteration 0, attempt 6.
accepted: False
generated: 2026-09-02T21:22:02.599612+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    unquoted = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", min_size=1)
    quoted = st.text(alphabet=st.printable.replace('"', '').replace("\\", "").replace("\n", "").replace("\r", ""), min_size=1).map(lambda x: f'"{x}"')
    return draw(st.one_of(unquoted, quoted))

@composite
def value(draw):
    basic_string = st.text(alphabet=st.printable.replace('"', '').replace("\\", ""), min_size=1).map(lambda x: f'"{x}"')
    literal_string = st.text(alphabet=st.printable.replace("'", ""), min_size=1).map(lambda x: f"'{x}'")
    integer = st.integers().map(str)
    float_value = st.floats().map(lambda x: f"{x:.3f}")
    boolean = st.one_of(st.just("true"), st.just("false"))
    return draw(st.one_of(basic_string, literal_string, integer, float_value, boolean))

@composite
def inline_table(draw):
    key_value_pairs = draw(st.lists(st.tuples(key(), value()), min_size=1, max_size=5))
    return "{" + ", ".join(f"{k}={v}" for k, v in key_value_pairs) + "}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), inline_table()), min_size=0, max_size=5))
    return "[" + ", ".join(elements) + "]"

@composite
def table(draw):
    key_value_pairs = draw(st.lists(st.tuples(key(), value()), min_size=1, max_size=5))
    return "[" + draw(key()) + "]\n" + "\n".join(f"{k} = {v}" for k, v in key_value_pairs)

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(table(), key().map(lambda k: f"{k} = {draw(value())}")), min_size=1, max_size=10))
    return "\n".join(elements)

toml_strategy = st.one_of(document(), array(), inline_table())