"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-09-03T14:18:14.466942+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
BASIC_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-.,:;!?@#$%^&*()+={}[]<>|~"
)
LITERAL_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-.,:;!?@#$%^&*()+={}[]<>|~\""
)
PLAIN_STRING_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-.,:;!?@#$%^&*()+={}[]<>|~😀🦄漢字"
)
ML_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "\t.,:;!?@#$%^&*()+={}[]<>|~\n"
)
ML_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "\t.,:;!?@#$%^&*()+={}[]<>|~\n\""
)

unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)
basic_key = st.text(
    alphabet=BASIC_KEY_CHARS, min_size=0, max_size=12
).map(lambda value: '"' + value + '"')
literal_key = st.text(
    alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
).map(lambda value: "'" + value + "'")

simple_key = st.one_of(unquoted_key, basic_key, literal_key)
dotted_key = st.lists(
    simple_key, min_size=2, max_size=6
).map(lambda parts: ".".join(parts))
key_strategy = st.one_of(simple_key, dotted_key)

escaped_piece = st.one_of(
    st.sampled_from([
        r"\n", r"\t", r"\r", r"\b", r"\f", r"\"", r"\\", r"\/",
        r"\u0041", r"\u03bb", r"\u20ac", r"\uD7FF",
        r"\U0001F600", r"\U0001F984",
    ]),
    st.tuples(
        st.sampled_from(["u", "U"]),
        st.text(
            alphabet="0123456789abcdefABCDEF",
            min_size=4,
            max_size=8,
        ),
    ).map(
        lambda parts: "\\" + parts[0] + (
            parts[1] if parts[0] == "u" else parts[1] + "00"
        )
    ),
)

basic_string = st.one_of(
    st.lists(
        st.one_of(
            st.text(
                alphabet=PLAIN_STRING_CHARS,
                min_size=1,
                max_size=8,
            ),
            escaped_piece,
        ),
        min_size=0,
        max_size=6,
    ).map(lambda parts: '"' + "".join(parts) + '"'),
    st.sampled_from([
        r'"\u0041"',
        r'"\u03bb"',
        r'"\u20ac"',
        r'"\U0001F600"',
        r'"\U0001F984"',
    ]),
)

literal_string = st.text(
    alphabet=PLAIN_STRING_CHARS + '"',
    min_size=0,
    max_size=30,
).map(lambda value: "'" + value + "'")

ml_basic_string = st.lists(
    st.one_of(
        st.text(alphabet=ML_BASIC_CHARS, min_size=1, max_size=12),
        escaped_piece,
    ),
    min_size=0,
    max_size=8,
).map(
    lambda parts: '"""' + "".join(parts).replace('"""', '""') + '"""'
)

ml_literal_string = st.text(
    alphabet=ML_LITERAL_CHARS, min_size=0, max_size=45
).map(
    lambda value: "'''" + value.replace("'''", "''") + "'''"
)

invalid_string = st.sampled_from([
    r'"\q"',
    r'"\x20"',
    r'"\u12"',
    r'"\U00110000"',
    '"unterminated',
    "'unterminated",
    '"""unterminated',
    "'''unterminated",
])

ordinary_decimal = st.one_of(
    st.integers(min_value=0, max_value=999999999).map(str),
    st.tuples(
        st.sampled_from(["1", "2", "7", "9"]),
        st.lists(
            st.integers(min_value=0, max_value=9).map(str),
            min_size=1,
            max_size=18,
        ),
    ).map(lambda parts: parts[0] + "_" + "_".join(parts[1])),
)

leading_zero_integer = st.sampled_from([
    "00", "000", "007", "0001", "09", "00_7", "000_001"
])

overflow_integer = st.sampled_from([
    "9223372036854775808",
    "9223372036854775809",
    "18446744073709551615",
    "-9223372036854775809",
    "-18446744073709551616",
])

decimal_integer = st.one_of(
    ordinary_decimal,
    leading_zero_integer,
    overflow_integer,
    st.sampled_from(["0", "1", "7", "42", "-0", "+0"]),
)

hex_integer = st.sampled_from([
    "0x0", "0x1", "0x7fffffff", "0xffffffffffffffff",
    "0xDEAD_BEEF", "0x8000_0000_0000_0000",
])
oct_integer = st.sampled_from([
    "0o0", "0o7", "0o755", "0o777_777_777_777",
])
bin_integer = st.one_of(
    st.sampled_from([
        "0b0", "0b1", "0b101010", "0b1111_0000",
        "0b" + "1" * 32,
    ]),
    st.tuples(
        st.integers(min_value=1, max_value=64),
        st.sampled_from(["0", "1"]),
    ).map(lambda parts: "0b" + parts[1] * parts[0]),
)
integer = st.one_of(
    decimal_integer, hex_integer, oct_integer, bin_integer
)

float_value = st.one_of(
    st.sampled_from([
        "0.0", "-0.0", "+0.0", "1.5", "3.141592653589793",
        "1_000.000_001", "9223372036854775808.0",
        "1e0", "1E+10", "-2e-9", "6.022e23", "1_000e-003",
    ]),
    st.sampled_from([
        "inf", "+inf", "-inf", "nan", "+nan", "-nan"
    ]),
    st.tuples(
        st.integers(min_value=0, max_value=999999).map(str),
        st.integers(min_value=1, max_value=25).map(str),
    ).map(lambda parts: parts[0] + "." + parts[1]),
    st.tuples(
        st.integers(min_value=0, max_value=999).map(str),
        st.integers(min_value=1, max_value=6).map(str),
    ).map(lambda parts: parts[0] + "e" + parts[1]),
)

date_only = st.tuples(
    st.integers(1970, 2100),
    st.integers(1, 12),
    st.integers(1, 28),
).map(lambda parts: f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}")

time_only = st.tuples(
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
).map(lambda parts: f"{parts[0]:02d}:{parts[1]:02d}:{parts[2]:02d}")

long_fraction = st.integers(
    min_value=1, max_value=9999999999999999999
).map(lambda value: f"{value:019d}")

local_date_time = st.tuples(
    date_only,
    time_only,
    long_fraction,
).map(lambda parts: parts[0] + "T" + parts[1] + "." + parts[2])

offset_date_time = st.tuples(
    date_only,
    time_only,
    long_fraction,
    st.sampled_from(["Z", "+00:00", "-07:00", "+23:59"]),
).map(
    lambda parts: (
        parts[0] + " " + parts[1] + "." + parts[2] + parts[3]
    )
)

date_time = st.one_of(
    date_only,
    time_only,
    local_date_time,
    offset_date_time,
)

scalar_value = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
    integer,
    float_value,
    date_time,
    st.sampled_from(["true", "false"]),
    invalid_string,
)


@composite
def recursive_value(draw):
    def extend(child):
        array_value = st.lists(
            st.one_of(child, child, child, array_value_placeholder),
            min_size=0,
            max_size=4,
        ).map(lambda values: "[" + ", ".join(values) + "]")

        inline_pair = st.tuples(key_strategy, child).map(
            lambda parts: parts[0] + " = " + parts[1]
        )
        inline_value = st.one_of(
            st.just("{}"),
            st.lists(
                inline_pair, min_size=1, max_size=4
            ).map(lambda values: "{ " + ", ".join(values) + " }"),
            st.lists(
                inline_pair, min_size=1, max_size=4
            ).map(lambda values: "{ " + ", ".join(values) + ", }"),
        )
        return st.one_of(
            array_value,
            array_value,
            inline_value,
            inline_value,
            child,
        )

    array_value_placeholder = scalar_value
    return draw(st.recursive(scalar_value, extend, max_leaves=45))


value_strategy = recursive_value()


@composite
def pair(draw):
    return draw(key_strategy) + " = " + draw(value_strategy)


@composite
def ordinary_document(draw):
    lines = draw(st.lists(
        st.one_of(
            pair(),
            key_strategy.map(lambda key: "[" + key + "]"),
            key_strategy.map(lambda key: "[[" + key + "]]"),
        ),
        min_size=1,
        max_size=10,
    ))
    return "\n".join(lines)


@composite
def malformed_document(draw):
    return draw(st.sampled_from([
        "x 1",
        "x = [",
        "x = { a = 1",
        'x = "unterminated',
        "x = 'unterminated",
        "x = { a = 1\n, b = 2}",
        "x = [1, 2,]",
        "x = { a = 1, }",
        "x = [[1]",
        "x = 1\n[broken",
    ]))


def indexed_key(index):
    return "k" + str(index)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48000, max_value=72000))
    opening = "".join(
        "[ " if index % 3 == 0 else "["
        for index in range(depth)
    )
    closing = "".join(
        " ]" if index % 3 == 1 else "]"
        for index in range(depth)
    )
    return "deep = " + opening + "0" + closing


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=42000, max_value=68000))
    result = "0"
    for index in range(depth):
        if index % 3 == 0:
            name = "k"
        elif index % 3 == 1:
            name = "'q'"
        else:
            name = '"r"'
        result = "{ " + name + " = " + result + " }"
    return "deep = " + result


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=48000, max_value=72000))
    parts = []
    for index in range(depth):
        if index % 3 == 0:
            parts.append("k" + str(index))
        elif index % 3 == 1:
            parts.append('"q' + str(index) + '"')
        else:
            parts.append("'r" + str(index) + "'")
    return ".".join(parts) + " = 0"


@composite
def long_document(draw):
    count = draw(st.integers(min_value=48000, max_value=70000))
    lines = []
    for index in range(count):
        key = indexed_key(index)
        if index % 5 == 0:
            lines.append(key + " = 0")
        elif index % 5 == 1:
            lines.append(key + " = [0, 1]")
        elif index % 5 == 2:
            lines.append(key + " = { a = 1, }")
        elif index % 5 == 3:
            lines.append("[" + key + "]")
        else:
            lines.append("[[" + key + "]]")
    return "\n".join(lines)


@composite
def sibling_document(draw):
    count = draw(st.integers(min_value=48000, max_value=70000))
    lines = []
    for index in range(count):
        key = indexed_key(index)
        if index % 4 == 0:
            value = "0"
        elif index % 4 == 1:
            value = "1.0"
        elif index % 4 == 2:
            value = '"x"'
        else:
            value = "0b101010"
        lines.append(key + " = " + value)
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 28),
    malformed_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    long_document(),
    sibling_document(),
)