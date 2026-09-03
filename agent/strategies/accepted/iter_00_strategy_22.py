"""Generated strategy - iteration 0, attempt 5.
accepted: True
generated: 2026-08-17T03:09:17.095013+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10))

@composite
def quoted_key(draw):
    return draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`", min_size=1, max_size=10).map(lambda x: f'"{x}"'))

@composite
def key(draw):
    return draw(st.one_of(unquoted_key(), quoted_key()))

@composite
def dotted_key(draw):
    return draw(st.lists(key(), min_size=2, max_size=5).map(lambda keys: ".".join(keys)))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=False, allow_infinity=False).map(str),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
    ))

@composite
def array_value(draw):
    return draw(st.lists(value(), min_size=0, max_size=10).map(lambda values: "[" + ", ".join(values) + "]"))

@composite
def inline_table_value(draw):
    return draw(st.lists(st.tuples(key(), value()), min_size=0, max_size=10).map(lambda pairs: "{" + ", ".join(f"{k} = {v}" for k, v in pairs) + "}"))

@composite
def pair(draw):
    return draw(st.tuples(key(), st.one_of(value(), array_value(), inline_table_value())).map(lambda pair: f"{pair[0]} = {pair[1]}"))

@composite
def table(draw):
    return draw(st.tuples(key(), st.lists(pair(), min_size=0, max_size=10)).map(lambda table: f"[{table[0]}]\n" + "\n".join(table[1])))

@composite
def document(draw):
    return draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10).map(lambda doc: "\n".join(doc)))

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "a." * n + "k"

@composite
def deep_document(draw):
    return draw(st.one_of(
        st.tuples(key(), deep_array()).map(lambda pair: f"{pair[0]} = {pair[1]}"),
        st.tuples(key(), deep_inline_table()).map(lambda pair: f"{pair[0]} = {pair[1]}"),
        st.tuples(deep_dotted_key(), value()).map(lambda pair: f"{pair[0]} = {pair[1]}"),
    ))

toml_strategy = st.one_of(document(), document(), deep_document())