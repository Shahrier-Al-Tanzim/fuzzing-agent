"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-09-02T23:19:40.445338+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?+-_/()[]{}<>@#$%^&*|~"
SAFE_LITERAL_CHARS = SAFE_BASIC_CHARS + "\\\"'="
UNICODE_CHARS = "😀🦄🚀𝄞𐐷"
ESCAPES = ["\\n", "\\t", "\\r", "\\b", "\\f", "\\\"", "\\\\", "\\/", "\\u0000", "\\u0041", "\\u20ac", "\\U0001f600"]

simple_unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)
quoted_key_part = st.text(
    alphabet=SAFE_BASIC_CHARS + UNICODE_CHARS, min_size=1, max_size=12
).map(lambda value: '"' + value + '"')
literal_key_part = st.text(
    alphabet=SAFE_LITERAL_CHARS + UNICODE_CHARS, min_size=1, max_size=12
).map(lambda value: "'" + value + "'")
simple_key = st.one_of(simple_unquoted_key, quoted_key_part, literal_key_part)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(
    lambda parts: ".".join(parts)
)
key = st.one_of(simple_key, dotted_key)

basic_piece = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS + UNICODE_CHARS, min_size=0, max_size=16),
    st.sampled_from(ESCAPES),
)
basic_string = st.lists(basic_piece, min_size=0, max_size=5).map(
    lambda parts: '"' + "".join(parts) + '"'
)
literal_string = st.text(
    alphabet=SAFE_LITERAL_CHARS + UNICODE_CHARS, min_size=0, max_size=24
).map(lambda value: "'" + value + "'")
ml_basic_body = st.text(
    alphabet=SAFE_BASIC_CHARS + " \t" + UNICODE_CHARS, min_size=0, max_size=30
)
ml_basic_string = ml_basic_body.map(lambda value: '"""' + value + '"""')
ml_literal_body = st.text(
    alphabet=SAFE_LITERAL_CHARS + "\n\r\t" + UNICODE_CHARS,
    min_size=0,
    max_size=30,
)
ml_literal_string = ml_literal_body.map(lambda value: "'''" + value + "'''")
invalid_string = st.sampled_from(
    ['"\\q"', '"\\x00"', '"unterminated', "'unterminated"]
)

zero_decimal = st.sampled_from(["0", "-0", "+0", "00", "000", "007", "-007"])
ordinary_decimal = st.integers(-1000000, 1000000).map(str)
large_decimal = st.sampled_from(
    [
        "9223372036854775807",
        "-9223372036854775808",
        "9223372036854775808",
        "-9223372036854775809",
        "999999999999999999999999999999",
        "-999999999999999999999999999999",
        "1_000_000",
        "9_223_372_036_854_775_807",
        "-9_223_372_036_854_775_808",
    ]
)
hex_integer = st.sampled_from(
    ["0x0", "0x7fffffff", "0xffffffffffffffff", "0xDEAD_BEEF", "0x1_0000"]
)
oct_integer = st.sampled_from(["0o0", "0o7", "0o755", "0o7_777_777"])
bin_integer = st.sampled_from(["0b0", "0b1", "0b101010", "0b1_0000_0000"])
integer = st.one_of(
    zero_decimal, ordinary_decimal, large_decimal, hex_integer, oct_integer, bin_integer
)

exponent = st.tuples(
    st.sampled_from(["1", "2", "10", "1000", "1_000", "999999"]),
    st.sampled_from(["e2", "E2", "e+10", "E-10", "e1_000"]),
).map(lambda pair: pair[0] + pair[1])
fraction = st.tuples(
    st.sampled_from(["0", "1", "3", "10", "1000"]),
    st.sampled_from(["1", "12", "1415", "999999", "1_000"]),
).map(lambda pair: pair[0] + "." + pair[1])
floating = st.one_of(
    exponent,
    fraction,
    st.tuples(st.sampled_from(["1", "12", "100"]), exponent).map(
        lambda pair: pair[0] + "." + pair[1][0] + pair[1][1]
    ),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
)

date_part = st.tuples(
    st.integers(1970, 2200),
    st.integers(1, 12),
    st.integers(1, 28),
).map(lambda value: f"{value[0]:04d}-{value[1]:02d}-{value[2]:02d}")
time_part = st.tuples(
    st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
).map(lambda value: f"{value[0]:02d}:{value[1]:02d}:{value[2]:02d}")
long_fraction = st.integers(1, 24).map(lambda count: "." + ("9" * count))
local_time = st.tuples(time_part, long_fraction).map(lambda value: value[0] + value[1])
offset = st.tuples(
    st.sampled_from(["Z", "+", "-"]),
    st.integers(0, 23),
    st.integers(0, 59),
).map(
    lambda value: "Z"
    if value[0] == "Z"
    else value[0] + f"{value[1]:02d}:{value[2]:02d}"
)
date_time = st.one_of(
    date_part,
    time_part,
    local_time,
    st.tuples(date_part, st.sampled_from(["T", "t", " "]), time_part).map(
        lambda value: "".join(value)
    ),
    st.tuples(date_part, st.sampled_from(["T", "t", " "]), time_part, offset).map(
        lambda value: value[0] + value[1] + value[2] + value[3]
    ),
    st.tuples(
        date_part, st.sampled_from(["T", "t", " "]), local_time, offset
    ).map(lambda value: value[0] + value[1] + value[2] + value[3]),
)

scalar = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
    invalid_string,
    integer,
    floating,
    date_time,
    st.sampled_from(["true", "false"]),
)


@composite
def recursive_value(draw):
    leaf = draw(scalar)
    return leaf


def _extend(children):
    array_value = st.lists(children, min_size=0, max_size=4).map(
        lambda values: "[" + ", ".join(values) + "]"
    )
    array_with_layout = st.lists(children, min_size=1, max_size=3).map(
        lambda values: "[\n" + ",\n".join(values) + ",\n]"
    )
    inline_pair = st.tuples(key, children).map(
        lambda pair: pair[0] + " = " + pair[1]
    )
    inline_table = st.lists(inline_pair, min_size=0, max_size=4).map(
        lambda pairs: "{ " + ", ".join(pairs) + " }"
    )
    duplicate_inline = st.tuples(key, children, children).map(
        lambda value: "{ "
        + value[0]
        + " = "
        + value[1]
        + ", "
        + value[0]
        + " = "
        + value[2]
        + " }"
    )
    return st.one_of(array_value, array_with_layout, inline_table, duplicate_inline)


value = st.recursive(scalar, _extend, max_leaves=35)

pair = st.tuples(key, value).map(lambda item: item[0] + " = " + item[1])
table_line = st.one_of(
    key.map(lambda name: "[" + name + "]"),
    key.map(lambda name: "[[" + name + "]]"),
)
normal_line = st.one_of(pair, table_line)

malformed_document = st.one_of(
    st.just("x ="),
    st.just("x = ["),
    st.just("x = {"),
    st.just('x = "unclosed'),
    st.just("x = 'unclosed"),
    st.just("x = { a = 1\n}"),
    st.just("x 1"),
    st.just("x = [1,"),
    st.just("x = { a = 1, }"),
    st.just("x = [1 2]"),
)

@composite
def document(draw):
    lines = draw(st.lists(normal_line, min_size=0, max_size=8))
    return "\n".join(lines)


@composite
def duplicate_document(draw):
    name = draw(simple_unquoted_key)
    first = draw(value)
    second = draw(value)
    return name + " = " + first + "\n" + name + " = " + second


@composite
def deep_array(draw):
    depth = draw(st.integers(min_value=48000, max_value=52000))
    return "[" * depth + "1" + "]" * depth


@composite
def deep_inline_table(draw):
    depth = draw(st.integers(min_value=80000, max_value=85000))
    return "{a=" * depth + "1" + "}" * depth


@composite
def deep_dotted_key(draw):
    depth = draw(st.integers(min_value=100000, max_value=105000))
    return "a." * depth + "k"


@composite
def deep_mixed_nesting(draw):
    depth = draw(st.integers(min_value=60000, max_value=65000))
    return "[{a=" * depth + "1" + "}]" * depth


@composite
def deep_quoted_mixed(draw):
    depth = draw(st.integers(min_value=20000, max_value=45000))
    return '[{"k"=' * depth + "1" + "}]" * depth


@composite
def deep_document(draw, shape):
    return "deep = " + draw(shape)


@composite
def many_siblings(draw):
    count = draw(st.integers(min_value=10000, max_value=40000))
    lines = ["[a]"] + [f"k{index} = 1" for index in range(count)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 20),
    duplicate_document(),
    malformed_document,
    deep_document(deep_array()),
    deep_document(deep_inline_table()),
    deep_document(deep_dotted_key()),
    deep_document(deep_mixed_nesting()),
    deep_document(deep_quoted_mixed()),
    many_siblings(),
)