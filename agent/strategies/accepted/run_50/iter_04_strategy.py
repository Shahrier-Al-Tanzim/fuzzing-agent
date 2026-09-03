"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-03T14:36:06.406413+00:00
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
HEX_DIGITS = "0123456789abcdefABCDEF"

unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=14
)
basic_key = st.text(
    alphabet=BASIC_KEY_CHARS, min_size=0, max_size=14
).map(lambda value: '"' + value + '"')
literal_key = st.text(
    alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=14
).map(lambda value: "'" + value + "'")
simple_key = st.one_of(unquoted_key, basic_key, literal_key)
dotted_key = st.lists(
    simple_key, min_size=2, max_size=8
).map(lambda parts: ".".join(parts))
key_strategy = st.one_of(simple_key, dotted_key)

escaped_piece = st.one_of(
    st.sampled_from([
        r"\n", r"\t", r"\r", r"\b", r"\f", r"\"", r"\\", r"\/",
        r"\u0041", r"\u03bb", r"\u20ac", r"\uD7FF",
        r"\U0001F600", r"\U0001F984",
    ]),
    st.text(alphabet=HEX_DIGITS, min_size=4, max_size=4).map(
        lambda value: "\\u" + value
    ),
    st.text(alphabet=HEX_DIGITS, min_size=8, max_size=8).map(
        lambda value: "\\U" + value
    ),
)

basic_string = st.lists(
    st.one_of(
        st.text(alphabet=PLAIN_STRING_CHARS, min_size=1, max_size=10),
        escaped_piece,
    ),
    min_size=0,
    max_size=8,
).map(lambda parts: '"' + "".join(parts) + '"')

literal_string = st.text(
    alphabet=PLAIN_STRING_CHARS + '"',
    min_size=0,
    max_size=32,
).map(lambda value: "'" + value + "'")

ml_basic_string = st.lists(
    st.one_of(
        st.text(alphabet=ML_BASIC_CHARS, min_size=1, max_size=14),
        escaped_piece,
    ),
    min_size=0,
    max_size=9,
).map(
    lambda parts: '"""' + "".join(parts).replace('"""', '""') + '"""'
)

ml_literal_string = st.text(
    alphabet=ML_LITERAL_CHARS, min_size=0, max_size=48
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
            max_size=20,
        ),
    ).map(lambda parts: parts[0] + "_" + "_".join(parts[1])),
)

leading_zero_integer = st.sampled_from([
    "00", "000", "007", "0001", "09", "00_7", "000_001", "00000042"
])

overflow_integer = st.sampled_from([
    "9223372036854775807",
    "9223372036854775808",
    "9223372036854775809",
    "18446744073709551615",
    "-9223372036854775808",
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
integer = st.one_of(decimal_integer, hex_integer, oct_integer, bin_integer)

float_value = st.one_of(
    st.sampled_from([
        "0.0", "-0.0", "+0.0", "1.5", "3.141592653589793",
        "1_000.000_001", "9223372036854775808.0",
        "1e0", "1E+10", "-2e-9", "6.022e23", "1_000e-003",
    ]),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
    st.tuples(
        st.integers(min_value=0, max_value=999999).map(str),
        st.integers(min_value=1, max_value=25).map(str),
    ).map(lambda parts: parts[0] + "." + parts[1]),
    st.tuples(
        st.integers(min_value=0, max_value=999).map(str),
        st.integers(min_value=1, max_value=8).map(str),
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
    min_value=0, max_value=9999999999999999999
).map(lambda value: f"{value:019d}")

local_date_time = st.tuples(
    date_only, time_only, long_fraction
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
    date_only, time_only, local_date_time, offset_date_time
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


def make_value(max_leaves, biased):
    def extend(child):
        if biased:
            array_elements = st.one_of(
                child, child, child, child, child, child, scalar_value
            )
            nested_pair = st.tuples(key_strategy, child).map(
                lambda parts: parts[0] + " = " + parts[1]
            )
            array_value = st.lists(
                array_elements, min_size=0, max_size=4
            ).map(lambda values: "[" + ", ".join(values) + "]")
            inline_value = st.one_of(
                st.just("{}"),
                st.lists(nested_pair, min_size=1, max_size=4).map(
                    lambda values: "{ " + ", ".join(values) + " }"
                ),
                st.lists(nested_pair, min_size=1, max_size=4).map(
                    lambda values: "{ " + ", ".join(values) + ", }"
                ),
            )
            return st.one_of(
                array_value, array_value, array_value,
                inline_value, inline_value, inline_value, child
            )

        array_elements = st.one_of(child, scalar_value)
        nested_pair = st.tuples(key_strategy, child).map(
            lambda parts: parts[0] + " = " + parts[1]
        )
        array_value = st.lists(
            array_elements, min_size=0, max_size=4
        ).map(lambda values: "[" + ", ".join(values) + "]")
        inline_value = st.one_of(
            st.just("{}"),
            st.lists(nested_pair, min_size=1, max_size=4).map(
                lambda values: "{ " + ", ".join(values) + " }"
            ),
            st.lists(nested_pair, min_size=1, max_size=4).map(
                lambda values: "{ " + ", ".join(values) + ", }"
            ),
        )
        return st.one_of(array_value, inline_value, child)

    return st.recursive(scalar_value, extend, max_leaves=max_leaves)


balanced_value = make_value(32, False)
biased_value = make_value(48, True)


@composite
def pair(draw, value_source=balanced_value):
    return draw(key_strategy) + " = " + draw(value_source)


@composite
def ordinary_document(draw):
    count = draw(st.integers(min_value=2, max_value=14))
    lines = []
    for index in range(count):
        kind = draw(st.integers(min_value=0, max_value=9))
        if kind <= 5:
            lines.append("k" + str(index) + " = " + draw(balanced_value))
        elif kind == 6:
            lines.append("[" + draw(key_strategy) + "]")
        elif kind == 7:
            lines.append("[[" + draw(key_strategy) + "]]")
        elif kind == 8:
            lines.append(
                "quoted" + str(index) + " = " +
                draw(st.one_of(basic_string, literal_string))
            )
        else:
            lines.append(
                "container" + str(index) + " = " +
                draw(st.one_of(
                    balanced_value, balanced_value, st.just("{}"),
                    st.just("{ a = 1, b = [true, false], }")
                ))
            )
    return "\n".join(lines)


@composite
def biased_document(draw):
    count = draw(st.integers(min_value=1, max_value=7))
    lines = []
    for index in range(count):
        kind = draw(st.integers(min_value=0, max_value=4))
        if kind == 0:
            lines.append("deep" + str(index) + " = " + draw(biased_value))
        elif kind == 1:
            lines.append("[" + draw(key_strategy) + "]")
        elif kind == 2:
            lines.append("[[" + draw(key_strategy) + "]]")
        elif kind == 3:
            lines.append(
                "x" + str(index) + " = { a = " +
                draw(biased_value) + ", }"
            )
        else:
            lines.append(
                "x" + str(index) + " = [" +
                draw(biased_value) + ", " +
                draw(balanced_value) + "]"
            )
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
        "x = [[1]",
        "x = 1\n[broken",
    ]))


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=90000, max_value=110000))
    quoted = draw(st.booleans())
    atom = draw(st.sampled_from(["0", "1", '"x"', "'y'", "true"]))
    openings = []
    closings = []
    for index in range(depth):
        if quoted and index % 5 == 0:
            openings.append("[ # level\n")
        elif index % 3 == 0:
            openings.append("[ ")
        else:
            openings.append("[")
        closings.append(" ]" if index % 4 == 1 else "]")
    return "deep = " + "".join(openings) + atom + "".join(reversed(closings))


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=90000, max_value=100000))
    quoted = draw(st.booleans())
    result = draw(st.sampled_from(["0", "1", '"x"', "'y'", "true"]))
    for index in range(depth):
        if quoted and index % 2 == 0:
            name = "'q'"
        elif quoted:
            name = '"r"'
        elif index % 3 == 0:
            name = "k"
        else:
            name = "m"
        if index % 7 == 0:
            result = "{ " + name + "=" + result + ", }"
        else:
            result = "{ " + name + "=" + result + " }"
    return "deep = " + result


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=90000, max_value=100000))
    quoted = draw(st.booleans())
    parts = []
    for index in range(depth):
        if quoted and index % 3 == 0:
            parts.append('"q' + str(index) + '"')
        elif quoted and index % 3 == 1:
            parts.append("'r" + str(index) + "'")
        else:
            parts.append("k" + str(index))
    return ".".join(parts) + " = " + draw(
        st.sampled_from(["0", "1", '"x"', "true"])
    )


def compact_name(number):
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number == 0:
        return "0"
    result = ""
    while number:
        result = alphabet[number % 36] + result
        number //= 36
    return result


@composite
def sibling_document(draw):
    count = draw(st.integers(min_value=90000, max_value=105000))
    mode = draw(st.integers(min_value=0, max_value=3))
    lines = []
    for index in range(count):
        key = "k" + compact_name(index)
        if mode == 0:
            value = "0"
        elif mode == 1:
            value = "1.0"
        elif mode == 2:
            value = '"x"'
        elif index % 2 == 0:
            value = "0b101010"
        else:
            value = "true"
        lines.append(key + "=" + value)
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 24),
    biased_document(),
    malformed_document(),
    deep_array_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_inline_document(),
    deep_dotted_document(),
    deep_dotted_document(),
    sibling_document(),
)