"""Generated strategy - iteration 3, attempt 4.
accepted: False
generated: 2026-09-02T20:39:24.948936+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite
import string

UNQUOTED_KEY_CHARS = string.ascii_letters + string.digits + "-_"
ESCAPE_CHARS = string.printable.replace('"', '').replace("\\", "").replace("\n", "").replace("\r", "")
HEX_DIGITS = string.hexdigits[:-6]  # Exclude lowercase 'abcdef'
OCT_DIGITS = "01234567"
BIN_DIGITS = "01"

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: x),
        st.text(alphabet=ESCAPE_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet=ESCAPE_CHARS, min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"{x}.{x}"),  # Dotted key
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=0, max_value=9223372036854775807).map(str),
        st.integers(min_value=-9223372036854775808, max_value=-1).map(str),
        st.floats().map(str),
        st.just('true'),
        st.just('false'),
        st.text(alphabet=ESCAPE_CHARS, min_size=1).map(lambda x: f'"{x}"'),
        st.text(alphabet=ESCAPE_CHARS, min_size=1).map(lambda x: f"'{x}'"),
        st.lists(value()).map(lambda lst: f"[{', '.join(lst)}]"),
        inline_table(),
        st.text(alphabet=ESCAPE_CHARS, min_size=1).map(lambda x: f'"""{x}"""'),  # Multi-line basic string
        st.text(alphabet=ESCAPE_CHARS, min_size=1).map(lambda x: f"'''{x}'''"),  # Multi-line literal string
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

@composite
def hex_int(draw):
    return draw(st.text(alphabet=HEX_DIGITS, min_size=1, max_size=10)).map(lambda x: f"0x{x}")

@composite
def oct_int(draw):
    return draw(st.text(alphabet=OCT_DIGITS, min_size=1, max_size=10)).map(lambda x: f"0o{x}")

@composite
def bin_int(draw):
    return draw(st.text(alphabet=BIN_DIGITS, min_size=1, max_size=10)).map(lambda x: f"0b{x}")

toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed(),
    many_siblings(),
    hex_int(),
    oct_int(),
    bin_int()
)