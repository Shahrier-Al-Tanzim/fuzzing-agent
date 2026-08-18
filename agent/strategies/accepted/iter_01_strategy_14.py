"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-08-16T18:28:00.652723+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"')
    ))

@composite
def dotted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
                .map(lambda x: f"{x}.a"))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                   st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        array(),
        inline_table(),
        ml_basic_string(),
        ml_literal_string(),
        escape_sequence(),
        unicode_escape(),
        non_ascii()
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    elements = draw(st.lists(
        st.one_of(value(), array(depth=depth + 1), array(depth=depth + 1),
                   array(depth=depth + 1), array(depth=depth + 1), inline_table())
    ))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    elements = draw(st.lists(
        st.tuples(key(), value())
    ))
    return f"{{{', '.join(f'{k} = {v}' for k, v in elements)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(
        st.one_of(pair(), table())
    ))
    return "\n".join(elements)

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
def ml_basic_string(draw):
    return draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
                         min_size=1, max_size=10).map(lambda x: f'"""{x}"""'))

@composite
def ml_literal_string(draw):
    return draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
                         min_size=1, max_size=10).map(lambda x: f"'''{x}'''"))

@composite
def escape_sequence(draw):
    return draw(st.text(alphabet="\\bfnrt", min_size=1, max_size=1))

@composite
def unicode_escape(draw):
    return draw(st.text(alphabet="u", min_size=1, max_size=1).map(lambda x: f"{x}XXXX"))

@composite
def non_ascii(draw):
    return draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=1).map(lambda x: f"{x}"))

toml_strategy = st.one_of(document(), document(), document(),
                          deep_array().map(lambda x: f"deep = {x}"),
                          deep_inline_table().map(lambda x: f"deep = {x}"),
                          deep_dotted_key().map(lambda x: f"{x} = 1"))