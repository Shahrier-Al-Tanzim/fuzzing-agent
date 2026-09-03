"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-17T03:19:45.313990+00:00
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
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`", min_size=1, max_size=10).map(lambda x: f'"""{x}"""'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`", min_size=1, max_size=10).map(lambda x: f"'''{x}'''"),
        st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=16).map(lambda x: f"0x{x}"),
        st.text(alphabet="012345678", min_size=1, max_size=22).map(lambda x: f"0o{x}"),
        st.text(alphabet="01", min_size=1, max_size=64).map(lambda x: f"0b{x}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
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
def array(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    return draw(st.one_of(
        value(),
        array(depth=depth + 1), array(depth=depth + 1),
        array(depth=depth + 1), array(depth=depth + 1),
    ))

@composite
def inline_table(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    return draw(st.one_of(
        value(),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1),
    ))

@composite
def document_depth_biased(draw):
    return draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10).map(lambda doc: "\n".join(doc)))

@composite
def pair_depth_biased(draw):
    return draw(st.tuples(key(), st.one_of(array(), inline_table(), value())).map(lambda pair: f"{pair[0]} = {pair[1]}"))

toml_strategy = st.one_of(document(), document(), deep_dotted_key().map(lambda k: f"{k} = 1"), deep_array().map(lambda a: f"a = {a}"), deep_inline_table().map(lambda it: f"a = {it}"))