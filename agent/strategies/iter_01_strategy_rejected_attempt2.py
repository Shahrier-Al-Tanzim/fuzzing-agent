"""Generated strategy - iteration 1, attempt 2.
accepted: False
generated: 2026-08-16T17:51:13.337797+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
UNQUOTED_KEY = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
QUOTED_KEY = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"')
KEY = st.one_of(UNQUOTED_KEY, QUOTED_KEY)

VALUE = st.one_of(
    st.integers(min_value=-2**63, max_value=2**63-1).map(str),
    st.floats(min_value=-1e10, max_value=1e10).map(str),
    st.booleans().map(lambda x: "true" if x else "false"),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"' + f'\\u{x:04x}'),
)

@composite
def pair(draw):
    k = draw(KEY)
    v = draw(VALUE)
    return f"{k} = {v}"

@composite
def table(draw):
    name = draw(KEY)
    return f"[{name}]"

@composite
def dotted_key(draw):
    k = draw(KEY)
    if draw(st.booleans()):
        return f"{k}.{draw(KEY)}"
    else:
        return k

@composite
def ml_basic_string(draw):
    return f'"""{draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10))}"""'

@composite
def ml_literal_string(draw):
    return f"'''{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10))}'''"

@composite
def escape_sequence(draw):
    return f"\\{draw(st.text(alphabet='\\/bfnrt', min_size=1, max_size=1))}"

@composite
def unicode_escape(draw):
    return f"\\u{draw(st.integers(min_value=0, max_value=0xFFFF)).map(lambda x: f'{x:04x}')}"

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(
        st.one_of(VALUE, array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1))))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(
        st.one_of(pair(), inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1))))
    return f"{{{', '.join(elements)}}}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

toml_strategy = document()