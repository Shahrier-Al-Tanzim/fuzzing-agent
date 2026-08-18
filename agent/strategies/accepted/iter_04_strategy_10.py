"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-16T17:54:27.678767+00:00
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
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"""{x}"""'),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'''{x}'''"),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"\\{x}"),  # escape_sequence
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"\\u{x}"),  # unicode_escape
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"\\{x}"),  # non_ascii
    st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0x{x:x}'),  # HEX_INT
    st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0o{x:o}'),  # OCT_INT
    st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0b{x:b}'),  # BIN_INT
)

DOTTED_KEY = KEY.map(lambda x: f"{x}.a")

ML_BASIC_STRING = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"""{x}"""')
ML_LITERAL_STRING = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'''{x}'''")

ESCAPE_SEQUENCE = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'\\{x}')

UNICODE_ESCAPE = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'\\u{x}')

NON_ASCII = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'\\{x}')

HEX_INT = st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0x{x:x}')

OCT_INT = st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0o{x:o}')

BIN_INT = st.integers(min_value=0, max_value=2**64-1).map(lambda x: f'0b{x:b}')

@composite
def pair(draw):
    k = draw(KEY)
    v = draw(st.one_of(
        VALUE,
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f'{x:020d}'),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f'{x:.20f}'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
    ))
    return f"{k} = {v}"

@composite
def table(draw):
    name = draw(KEY)
    return f"[{name}]"

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(
        st.one_of(array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1), array(depth=depth + 1), VALUE)))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw, depth=0):
    if depth >= 20000:
        return draw(VALUE)
    elements = draw(st.lists(
        st.one_of(inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1), inline_table(depth=depth + 1), pair())))
    return f"{{{', '.join(elements)}}}"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

@composite
def document_depth_biased(draw):
    elements = draw(st.lists(st.one_of(pair_depth_biased(), table())))
    return "\n".join(elements)

@composite
def pair_depth_biased(draw):
    k = draw(KEY)
    v = draw(st.one_of(
        VALUE,
        array(depth=0),
        array(depth=0),
        array(depth=0),
        array(depth=0),
        inline_table(depth=0),
        inline_table(depth=0),
        inline_table(depth=0),
        inline_table(depth=0),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f'{x:020d}'),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f'{x:.20f}'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=10).map(lambda x: f"'{x}'"),
    ))
    return f"{k} = {v}"

toml_strategy = st.one_of(document(), document_depth_biased())