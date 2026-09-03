"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-03T14:06:06.478638+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?@#$%^&*()+={}[]<>|~"
LITERAL_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?@#$%^&*()+={}[]<>|~"
PLAIN_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?@#$%^&*()+={}[]<>|~😀🦄漢字"
ML_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t.,:;!?@#$%^&*()+={}[]<>|~\n"
ML_LITERAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t.,:;!?@#$%^&*()+={}[]<>|~\n\""


unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)

basic_key = st.text(
    alphabet=BASIC_KEY_CHARS, min_size=0, max_size=12
).map(lambda s: '"' + s + '"')

literal_key = st.text(
    alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
).map(lambda s: "'" + s + "'")

simple_key = st.one_of(unquoted_key, basic_key, literal_key)

dotted_key = st.lists(
    simple_key, min_size=2, max_size=6
).map(lambda parts: ".".join(parts))

key_strategy = st.one_of(simple_key, dotted_key)


escaped_piece = st.sampled_from([
    r"\n", r"\t", r"\r", r"\b", r"\f", r"\"", r"\\", r"\/",
    r"\u0000", r"\u0041", r"\u03bb", r"\u20ac", r"\uD7FF",
    r"\U0001F600", r"\U0001F984",
])

basic_string = st.lists(
    st.one_of(
        st.text(alphabet=PLAIN_STRING_CHARS, min_size=1, max_size=8),
        escaped_piece,
    ),
    min_size=0,
    max_size=6,
).map(lambda parts: '"' + "".join(parts) + '"')

literal_string = st.text(
    alphabet=LITERAL_KEY_CHARS + "😀🦄漢字", min_size=0, max_size=30
).map(lambda s: "'" + s + "'")

ml_basic_string = st.lists(
    st.one_of(
        st.text(alphabet=ML_BASIC_CHARS, min_size=1, max_size=12),
        escaped_piece,
    ),
    min_size=0,
    max_size=8,
).map(lambda parts: '"""' + "".join(parts).replace('"""', '""') + '"""')

ml_literal_string = st.text(
    alphabet=ML_LITERAL_CHARS, min_size=0, max_size=45
).map(lambda s: "'''" + s.replace("'''", "''") + "'''")

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


decimal_digits = st.one_of(
    st.sampled_from(["0", "1", "7", "42", "007", "0001", "09"]),
    st.tuples(
        st.integers(min_value=1, max_value=9).map(str),
        st.lists(
            st.integers(min_value=0, max_value=9).map(str),
            min_size=1,
            max_size=18,
        ),
    ).map(lambda p: p[0] + "_" + "_".join(p[1])),
    st.sampled_from([
        "9223372036854775807",
        "9223372036854775808",
        "9223372036854775809",
        "-9223372036854775808",
        "-9223372036854775809",
        "18446744073709551615",
        "-0",
        "+0",
    ]),
)

hex_integer = st.sampled_from([
    "0x0", "0x1", "0x7fffffff", "0xffffffffffffffff",
    "0xDEAD_BEEF", "0x8000_0000_0000_0000",
])

oct_integer = st.sampled_from([
    "0o0", "0o7", "0o755", "0o777_777_777_777",
])

bin_integer = st.sampled_from([
    "0b0", "0b1", "0b101010", "0b1111_0000", "0b" + "1" * 32,
])

integer = st.one_of(decimal_digits, hex_integer, oct_integer, bin_integer)

float_value = st.one_of(
    st.sampled_from([
        "0.0", "-0.0", "+0.0", "1.5", "3.141592653589793",
        "1_000.000_001", "9223372036854775808.0",
        "1e0", "1E+10", "-2e-9", "6.022e23", "1_000e-003",
        "inf", "+inf", "-inf", "nan", "+nan", "-nan",
    ]),
    st.tuples(
        st.integers(min_value=0, max_value=999999).map(str),
        st.integers(min_value=1, max_value=25).map(str),
    ).map(lambda p: p[0] + "." + p[1]),
)

date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda t: (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T"
            f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        )
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(1, 9999999999999999999),
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]:019d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
        st.sampled_from(["Z", "+00:00", "-07:00", "+23:59"]),
    ).map(
        lambda t: (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} "
            f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:019d}{t[7]}"
        )
    ),
)

scalar_value = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
    integer,
    float_value,
    st.sampled_from(["true", "false"]),
    date_time,
    invalid_string,
)


@composite
def recursive_value(draw):
    def extend(child):
        array_value = st.lists(
            child, min_size=0, max_size=4
        ).map(lambda xs: "[" + ", ".join(xs) + "]")

        inline_pair = st.tuples(key_strategy, child).map(
            lambda p: p[0] + " = " + p[1]
        )
        duplicate_inline = st.tuples(
            key_strategy, child, child
        ).map(
            lambda p: (
                p[0] + " = " + p[1] + ", " +
                p[0] + " = " + p[2]
            )
        )
        inline_value = st.one_of(
            st.just("{}"),
            st.lists(inline_pair, min_size=1, max_size=4).map(
                lambda xs: "{ " + ", ".join(xs) + " }"
            ),
            st.lists(inline_pair, min_size=1, max_size=4).map(
                lambda xs: "{ " + ", ".join(xs) + ", }"
            ),
            duplicate_inline.map(lambda x: "{ " + x + " }"),
        )
        return st.one_of(
            array_value,
            array_value,
            inline_value,
            inline_value,
        )

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
            key_strategy.map(lambda k: "[" + k + "]"),
            key_strategy.map(lambda k: "[[" + k + "]]"),
        ),
        min_size=0,
        max_size=12,
    ))
    return "\n".join(lines)


@composite
def duplicate_document(draw):
    k = draw(key_strategy)
    first = draw(value_strategy)
    second = draw(value_strategy)
    return k + " = " + first + "\n" + k + " = " + second


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


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48001, max_value=60000))
    return "deep = " + ("[" * depth) + "0" + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=48001, max_value=60000))
    result = "0"
    for i in range(depth):
        name = "k" + str(i) if i % 2 == 0 else "'q" + str(i) + "'"
        result = "{ " + name + " = " + result + " }"
    return "deep = " + result


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=48001, max_value=60000))
    parts = []
    for i in range(depth):
        if i % 3 == 0:
            parts.append("k" + str(i))
        elif i % 3 == 1:
            parts.append('"q' + str(i) + '"')
        else:
            parts.append("'r" + str(i) + "'")
    return ".".join(parts) + " = 0"


@composite
def long_document(draw):
    count = draw(st.integers(min_value=48001, max_value=60000))
    lines = []
    for i in range(count):
        if i % 4 == 0:
            lines.append("k" + str(i) + " = 0")
        elif i % 4 == 1:
            lines.append('"q' + str(i) + '" = [0, 1, 2]')
        elif i % 4 == 2:
            lines.append("k" + str(i) + " = { a = 1, }")
        else:
            lines.append("[table" + str(i) + "]")
    return "\n".join(lines)


@composite
def sibling_document(draw):
    count = draw(st.integers(min_value=3000, max_value=12000))
    value = draw(st.one_of(
        st.just("0"),
        st.just("1.0"),
        st.just('"x"'),
        st.just("{ a = 1 }"),
    ))
    lines = []
    for i in range(count):
        if i % 5 == 0:
            lines.append('"key ' + str(i) + '" = ' + value)
        else:
            lines.append("key_" + str(i) + " = " + value)
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    duplicate_document(),
    duplicate_document(),
    malformed_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    long_document(),
    sibling_document(),
)