"""Generated strategy - iteration 0, attempt 7.
accepted: True
generated: 2026-09-02T21:12:02.982180+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
ESCAPED_CHARS = ['"', '\\', '\n', '\r', '\t']
BASIC_STRING_CHARS = st.text(alphabet=st.characters(blacklist_categories=("C", "Z")), min_size=1).map(lambda x: f'"{x}"')
LITERAL_STRING_CHARS = st.text(alphabet=st.characters(blacklist_categories=("C", "Z")), min_size=1).map(lambda x: f"'{x}'")
BOOLEAN = st.one_of(st.just("true"), st.just("false"))
INF_NAN = st.one_of(st.just("inf"), st.just("-inf"), st.just("nan"))
LEADING_ZERO_INT = st.integers(min_value=0).filter(lambda x: str(x).startswith('0') and x != 0).map(str)
EXTREME_INT = st.one_of(st.integers(-9223372036854775808, 9223372036854775807), st.integers(9223372036854775808, 9223372036854775808))
FLOAT = st.floats(allow_nan=True, allow_infinity=True).map(str)
DATE_TIME = st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}")
ARRAY = st.recursive(st.one_of(BASIC_STRING_CHARS, BOOLEAN, INF_NAN, LEADING_ZERO_INT, EXTREME_INT, FLOAT, DATE_TIME), lambda x: st.lists(x).map(lambda lst: f"[{', '.join(lst)}]"))
INLINE_TABLE = st.recursive(st.one_of(BASIC_STRING_CHARS, BOOLEAN, INF_NAN, LEADING_ZERO_INT, EXTREME_INT, FLOAT, DATE_TIME), lambda x: st.lists(st.tuples(BASIC_STRING_CHARS, x)).map(lambda lst: "{" + ", ".join(f"{k}={v}" for k, v in lst) + "}"))

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        BASIC_STRING_CHARS,
        LITERAL_STRING_CHARS
    ))

@composite
def key_value(draw):
    k = draw(key())
    v = draw(st.one_of(BASIC_STRING_CHARS, LITERAL_STRING_CHARS, BOOLEAN, INF_NAN, LEADING_ZERO_INT, EXTREME_INT, FLOAT, DATE_TIME, ARRAY, INLINE_TABLE))
    return f"{k} = {v}"

@composite
def table(draw):
    return f"[{draw(key())}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(key_value(), table()), min_size=1))
    return "\n".join(elements)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60000, max_value=100000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85000, max_value=115000))
    return "{a=" * n + "1" + "}" * n

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array(),
    deep_inline_table(),
    many_siblings()
)