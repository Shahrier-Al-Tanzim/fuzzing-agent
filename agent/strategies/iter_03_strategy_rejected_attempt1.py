"""Generated strategy - iteration 3, attempt 1.
accepted: False
generated: 2026-09-02T20:46:18.175963+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
ESCAPE_SEQUENCES = ['\\', '\b', '\f', '\n', '\r', '\t', '\v', '"', "'"]
UNICODE_ESCAPE = lambda x: f'\\u{x:04x}'
HEX_INT = lambda x: f"0x{x:x}"
OCT_INT = lambda x: f"0o{x:o}"
BIN_INT = lambda x: f"0b{x:b}"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: x),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"{x}.{x}"),  # Dotted key
    ))

@composite
def escape_sequence(draw):
    return draw(st.sampled_from(ESCAPE_SEQUENCES))

@composite
def unicode_escape(draw):
    return draw(st.integers(min_value=0, max_value=0xFFFF)).map(UNICODE_ESCAPE)

@composite
def hex_int(draw):
    return draw(st.integers(min_value=0)).map(HEX_INT)

@composite
def oct_int(draw):
    return draw(st.integers(min_value=0)).map(OCT_INT)

@composite
def bin_int(draw):
    return draw(st.integers(min_value=0)).map(BIN_INT)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=0, max_value=9223372036854775807).map(str),
        st.integers(min_value=-9223372036854775808, max_value=-1).map(str),
        st.floats().map(str),
        st.just('true'),
        st.just('false'),
        st.text(min_size=1).map(lambda x: f'"{x}"'),
        st.text(min_size=1).map(lambda x: f"'{x}'"),
        st.lists(value()).map(lambda lst: f"[{', '.join(lst)}]"),
        inline_table(),
        st.text(min_size=1).map(lambda x: f'"""{x}"""'),  # Multi-line basic string
        st.text(min_size=1).map(lambda x: f"'''{x}'''"),  # Multi-line literal string
        escape_sequence().map(lambda esc: f'"{esc}"'),
        unicode_escape(),
        hex_int(),
        oct_int(),
        bin_int(),
    ))

@composite
def inline_table(draw):
    keyvals = draw(st.lists(st.tuples(key(), value()), min_size=1, max_size=5))
    return "{" + ", ".join(f"{k}={v}" for k, v in keyvals) + "}"

@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def table(draw):
    k = draw(key())
    return f"[{k}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=1))
    return "\n".join(elements)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=90_000, max_value=100_000))
    return "a." * n + "k"

@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[{a=" * n + "1" + "}]" * n

@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    return '[{"k"=' * n + "1" + "}]" * n

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed(),
    many_siblings()
)