"""Generated strategy - iteration 4, attempt 2.
accepted: False
generated: 2026-09-02T20:52:58.225793+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite
import string

UNQUOTED_KEY_CHARS = string.ascii_letters + string.digits + "-_"
ESCAPE_SEQUENCES = ['\\', '\b', '\f', '\n', '\r', '\t', '\v', '"', "'"]
UNICODE_ESCAPE = lambda x: f'\\u{x:04x}'

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: x),
        st.text(alphabet=string.printable.replace('"', '').replace("\\", "").replace("\n", "").replace("\r", ""), min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(alphabet=string.printable.replace('"', '').replace("\\", "").replace("\n", "").replace("\r", ""), min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"{x}.{x}"),  # Dotted key
    ))

@composite
def escape_sequence(draw):
    return draw(st.one_of(
        st.sampled_from(ESCAPE_SEQUENCES),
        st.integers(min_value=0, max_value=0xFFFF).map(UNICODE_ESCAPE)
    ))

@composite
def hex_int(draw):
    return draw(st.integers(min_value=0).map(lambda x: f"0x{x:x}"))

@composite
def oct_int(draw):
    return draw(st.integers(min_value=0).map(lambda x: f"0o{x:o}"))

@composite
def bin_int(draw):
    return draw(st.integers(min_value=0).map(lambda x: f"0b{x:b}"))

@composite
def leading_zero_int(draw):
    return draw(st.integers(min_value=1, max_value=9).map(lambda x: f"0{x}"))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=0, max_value=9223372036854775807).map(str),
        st.integers(min_value=-9223372036854775808, max_value=-1).map(str),
        st.floats().map(str),
        st.just('true'),
        st.just('false'),
        st.lists(escape_sequence()).map(lambda lst: f'"{"".join(lst)}"'),
        st.lists(escape_sequence()).map(lambda lst: f"'{''.join(lst)}'"),
        st.lists(value()).map(lambda lst: f"[{', '.join(lst)}]"),
        inline_table(),
        st.text(min_size=1).map(lambda x: f'"""{x}"""'),  # Multi-line basic string
        st.text(min_size=1).map(lambda x: f"'''{x}'''"),  # Multi-line literal string
        hex_int(),
        oct_int(),
        bin_int(),
        leading_zero_int(),
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
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 20),
    many_siblings()
)