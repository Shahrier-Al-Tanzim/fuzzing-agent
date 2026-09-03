"""Generated strategy - iteration 0, attempt 5.
accepted: False
generated: 2026-09-02T23:21:27.184651+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~\n\r\t"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !\"#$%&()*+,-./:;<=>?@[]^_`{|}~"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !\"#$%&()*+,-./:;<=>?@[]^_`{|}~\n\r\t"

unquoted_key = st.text(alphabet=UNQUOTED, min_size=1, max_size=12)
basic_key_body = st.text(alphabet=BASIC_SAFE, min_size=0, max_size=12)
literal_key_body = st.text(alphabet=LITERAL_SAFE.replace("'", ""), min_size=0, max_size=12)

basic_key = basic_key_body.map(lambda s: '"' + s + '"')
literal_key = literal_key_body.map(lambda s: "'" + s + "'")
simple_key = st.one_of(unquoted_key, basic_key, literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda xs: ".".join(xs))
key = st.one_of(simple_key, dotted_key)

basic_escape = st.sampled_from([
    "\\n", "\\t", "\\r", "\\b", "\\f", '\\"', "\\\\", "\\/", "\\u0000",
    "\\u0041", "\\u03bb", "\\u20ac", "\\uD7FF", "\\uFFFF"
])
basic_body = st.one_of(
    st.text(alphabet=BASIC_SAFE, min_size=0, max_size=24),
    basic_escape,
    st.sampled_from(["😀", "🦄", "𝄞", "𐀀", "€"])
)
basic_string = st.lists(basic_body, min_size=0, max_size=6).map(
    lambda xs: '"' + "".join(xs) + '"'
)

literal_string = st.text(
    alphabet=LITERAL_SAFE.replace("'", ""),
    min_size=0,
    max_size=32,
).map(lambda s: "'" + s + "'")

ml_basic_string = st.text(
    alphabet=ML_BASIC_SAFE,
    min_size=0,
    max_size=48,
).map(lambda s: '"""' + s.replace('"""', '" ""') + '"""')

ml_literal_string = st.text(
    alphabet=ML_LITERAL_SAFE.replace("'", ""),
    min_size=0,
    max_size=48,
).map(lambda s: "'''" + s + "'''")

string_value = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
)

decimal_numbers = st.sampled_from([
    "0", "-0", "1", "-1", "42", "-42", "007", "0000", "1_000", "12_345_678",
    "9223372036854775807", "-9223372036854775808",
    "9223372036854775808", "-9223372036854775809",
    "999999999999999999999999", "-999999999999999999999999",
])
based_numbers = st.sampled_from([
    "0x0", "0x1", "0xdead_beef", "0o0", "0o755", "0o12_345",
    "0b0", "0b1", "0b1010_0101",
])
integer_value = st.one_of(decimal_numbers, based_numbers)

float_value = st.sampled_from([
    "0.0", "-0.0", "+0.0", "1.5", "-1.5", "10.000_001",
    "1e0", "1E+10", "-2e-3", "1_000.25", "1.0e+999",
    "inf", "+inf", "-inf", "nan", "+nan", "-nan",
])

date_value = st.tuples(
    st.integers(1970, 2100),
    st.integers(1, 12),
    st.integers(1, 28),
).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}")

time_value = st.tuples(
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
).map(lambda x: f"{x[0]:02d}:{x[1]:02d}:{x[2]:02d}")

local_datetime = st.tuples(date_value, time_value).map(
    lambda x: x[0] + "T" + x[1]
)
offset_datetime = st.tuples(
    date_value,
    time_value,
    st.integers(-12, 14),
    st.integers(0, 59),
    st.integers(0, 9_999_999_999_999_999_999),
).map(
    lambda x: (
        x[0] + "T" + x[1] + f"{x[2]:+03d}:{x[3]:02d}."
        + f"{x[4]:019d}"
    )
)
date_time_value = st.one_of(
    date_value,
    time_value,
    local_datetime,
    offset_datetime,
)

scalar_value = st.one_of(
    string_value,
    integer_value,
    float_value,
    st.sampled_from(["true", "false"]),
    date_time_value,
)

@composite
def array_value(draw, values):
    items = draw(st.lists(values, min_size=0, max_size=5))
    if not items:
        return "[]"
    separator = draw(st.sampled_from([", ", ",\n", ",\n# array item\n"]))
    result = "[" + separator.join(items)
    if draw(st.booleans()):
        result += ","
    return result + "]"

@composite
def inline_table_value(draw, values):
    count = draw(st.integers(0, 4))
    if count == 0:
        return "{}"
    pairs = []
    for _ in range(count):
        pairs.append(draw(key) + " = " + draw(values))
    result = "{ " + ", ".join(pairs)
    if draw(st.booleans()):
        result += ","
    return result + " }"

def recursive_values(max_leaves):
    return st.recursive(
        scalar_value,
        lambda values: st.one_of(
            array_value(values),
            array_value(values),
            inline_table_value(values),
            inline_table_value(values),
        ),
        max_leaves=max_leaves,
    )

ordinary_values = recursive_values(35)
broader_values = recursive_values(90)

@composite
def pair(draw, values=ordinary_values):
    return draw(key) + " = " + draw(values)

@composite
def table_line(draw):
    return draw(st.one_of(
        key.map(lambda k: "[" + k + "]"),
        key.map(lambda k: "[[" + k + "]]"),
    ))

@composite
def valid_document(draw, values=ordinary_values):
    count = draw(st.integers(1, 7))
    lines = []
    for _ in range(count):
        if draw(st.integers(0, 4)):
            lines.append(draw(pair(values)))
        else:
            lines.append(draw(table_line()))
    return "\n".join(lines)

@composite
def broad_document(draw):
    count = draw(st.integers(1, 6))
    lines = []
    for _ in range(count):
        if draw(st.booleans()):
            lines.append(draw(pair(broader_values)))
        else:
            lines.append(draw(table_line()))
    return "\n".join(lines)

duplicate_top_level = st.tuples(key, ordinary_values).map(
    lambda x: x[0] + " = " + x[1] + "\n" + x[0] + " = " + x[1]
)

duplicate_inline = st.tuples(key, key, ordinary_values, ordinary_values).map(
    lambda x: "x = { " + x[0] + " = " + x[2] + ", " + x[1]
    + " = " + x[3] + ", " + x[0] + " = " + x[2] + " }"
)

malformed_basic = st.sampled_from([
    'x = "bad\\q"',
    'x = "unterminated',
    'x = "line\nbreak"',
    'x = "\\u12"',
    'x = "\\U0000ZZZZ"',
])
malformed_structural = st.sampled_from([
    "x = { a = 1,\n b = 2 }",
    "x = { a = 1, }",
    "x = [1, 2,",
    "x = { a = 1",
    "x = [1, 2",
    "x 1",
    "[broken",
    "[[broken]]",
])
malformed_document = st.one_of(malformed_basic, malformed_structural)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=48_000, max_value=60_000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=80_000, max_value=100_000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=90_000, max_value=130_000))
    return "a." * n + "k"

@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[{a=" * n + "1" + "}]" * n

@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    return '[{"k"=' * n + "1" + "}]" * n

def deep_document(shape):
    return shape.map(lambda value: "deep = " + value)

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"]
    for i in range(n):
        lines.append(f"k{i} = 1")
    return "\n".join(lines)

empty_document = st.just("")

toml_strategy = st.one_of(
    *([valid_document()] * 20),
    broad_document(),
    duplicate_top_level,
    duplicate_inline,
    malformed_document,
    empty_document,
    deep_document(deep_array()),
    deep_document(deep_inline_table()),
    deep_document(deep_dotted_key()),
    deep_document(deep_mixed_nesting()),
    deep_document(deep_quoted_mixed()),
    many_siblings(),
)