"""Generated strategy - iteration 1, attempt 2.
accepted: True
generated: 2026-08-16T18:18:29.674586+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`\\|[];\"' ", min_size=1, max_size=10).map(lambda x: f'"{x}"')
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000000, max_value=1000000).map(str),
        st.floats(min_value=-1000000, max_value=1000000).map(str),
        st.text(min_size=1, max_size=10),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-={}:<>?,./~`\\|[];\"' ", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T00:00:00"),
        st.lists(st.integers(min_value=-1000000, max_value=1000000)).map(lambda x: "[" + ", ".join(map(str, x)) + "]"),
        st.lists(st.text(min_size=1, max_size=10)).map(lambda x: "[" + ", ".join(x) + "]"),
        st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=10)).map(lambda x: "{" + ", ".join(f"{k}={v}" for k, v in x.items()) + "}"),
        st.text(min_size=3, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=3, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=3, max_size=10).map(lambda x: f'"""{x}"""'),
        st.text(min_size=3, max_size=10).map(lambda x: f"'''{x}'''"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59), st.text(min_size=1, max_size=10))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]}"),
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def table(draw):
    return f"[{draw(key())}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

@composite
def array(draw, depth=0):
    if depth >= 12:
        return draw(value())
    return draw(st.one_of(
        value(),
        array(depth=depth + 1), array(depth=depth + 1),
        array(depth=depth + 1), array(depth=depth + 1),
    ))

@composite
def inline_table(draw, depth=0):
    if depth >= 12:
        return draw(value())
    return draw(st.one_of(
        value(),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1),
    ))

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=200, max_value=5000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=200, max_value=5000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=200, max_value=5000))
    return "a." * n + "k"

toml_strategy = st.one_of(document(), document(), deep_array().map(lambda x: f"deep = {x}"))