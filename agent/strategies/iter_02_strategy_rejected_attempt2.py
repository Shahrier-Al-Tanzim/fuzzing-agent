"""Generated strategy - iteration 2, attempt 2.
accepted: False
generated: 2026-09-03T13:12:36.153083+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():;"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():;\""
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/:;()"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/:;()\""

QUOTED_KEY_SAFE = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():;"
)

@composite
def basic_string(draw):
    ordinary = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=24))
    escapes = draw(
        st.lists(
            st.sampled_from(
                [
                    "\\n",
                    "\\t",
                    "\\r",
                    "\\b",
                    "\\f",
                    "\\\"",
                    "\\\\",
                    "\\/",
                    "\\u0000",
                    "\\u0041",
                    "\\u03bb",
                    "\\U0001f600",
                ]
            ),
            min_size=0,
            max_size=8,
        )
    )
    return '"' + "".join(draw(st.permutations([ordinary] + escapes))) + '"'


@composite
def unicode_basic_string(draw):
    pieces = draw(
        st.lists(
            st.one_of(
                st.text(alphabet=BASIC_SAFE, min_size=0, max_size=8),
                st.sampled_from(
                    [
                        "\\u0000",
                        "\\u0041",
                        "\\u03bb",
                        "\\u20ac",
                        "\\u4e2d",
                        "\\U0001f600",
                        "\\U0001f642",
                    ]
                ),
            ),
            min_size=1,
            max_size=8,
        )
    )
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    return "'" + draw(
        st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=28)
    ) + "'"


@composite
def multiline_basic(draw):
    return '"""' + draw(
        st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=48)
    ) + '"""'


@composite
def multiline_literal(draw):
    return "'''" + draw(
        st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=48)
    ) + "'''"


def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.text(
        alphabet=QUOTED_KEY_SAFE, min_size=1, max_size=12
    ).map(lambda value: '"' + value + '"')


def simple_key():
    return st.one_of(unquoted_key(), quoted_key(), literal_string())


@composite
def key(draw):
    first = draw(simple_key())
    rest = draw(st.lists(simple_key(), min_size=0, max_size=3))
    return ".".join([first] + rest)


valid_decimal = st.one_of(
    st.just("0"),
    st.integers(min_value=1, max_value=999999).map(str),
    st.tuples(
        st.integers(min_value=1, max_value=999999),
        st.integers(min_value=1, max_value=999999),
    ).map(lambda pair: str(pair[0]) + "_" + str(pair[1])),
)

integer_value = st.one_of(
    valid_decimal,
    st.sampled_from(
        [
            "-0",
            "007",
            "00042",
            "0_0",
            "12_34_567",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "9_223_372_036_854_775_807",
            "-9_223_372_036_854_775_808",
        ]
    ),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(
        lambda number: "0x" + format(number, "x")
    ),
    st.integers(min_value=0, max_value=0o777777777).map(
        lambda number: "0o" + format(number, "o")
    ),
    st.integers(min_value=0, max_value=0b111111111).map(
        lambda number: "0b" + format(number, "b")
    ),
)

float_value = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "1.0",
            "-1.5",
            "3.1415926535",
            "1e0",
            "-1E+10",
            "6.02e23",
            "1_000.5",
            "9.9e-9",
            "inf",
            "+inf",
            "-inf",
            "nan",
            "+nan",
            "-nan",
        ]
    ),
    st.tuples(
        st.integers(min_value=-999999, max_value=999999).map(str),
        st.integers(min_value=0, max_value=999999).map(
            lambda number: f"{number:06d}"
        ),
        st.integers(min_value=-30, max_value=30),
    ).map(lambda value: f"{value[0]}.{value[1]}e{value[2]:+d}"),
    st.tuples(
        valid_decimal,
        st.integers(min_value=1, max_value=999999).map(
            lambda number: f"{number:06d}"
        ),
    ).map(lambda value: f"{value[0]}.{value[1]}"),
)

date_value = st.one_of(
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda value: f"{value[0]:04d}-{value[1]:02d}-{value[2]:02d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda value: (
            f"{value[0]:04d}-{value[1]:02d}-{value[2]:02d}T"
            f"{value[3]:02d}:{value[4]:02d}:{value[5]:02d}"
        )
    ),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
        st.integers(-12, 12),
        st.integers(0, 59),
    ).map(
        lambda value: (
            f"{value[0]:04d}-{value[1]:02d}-{value[2]:02d} "
            f"{value[3]:02d}:{value[4]:02d}:{value[5]:02d}."
            f"{value[6]:019d}{value[7]:+03d}:{value[8]:02d}"
        )
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda value: f"{value[0]:02d}:{value[1]:02d}:{value[2]:02d}"),
)

scalar_value = st.one_of(
    st.just("0"),
    st.just("1"),
    st.just("true"),
    st.just("false"),
    unicode_basic_string(),
    basic_string(),
    literal_string(),
    multiline_basic(),
    multiline_literal(),
    integer_value,
    float_value,
    date_value,
    st.sampled_from(['"\\q"', '"\\x"', '"\\uD800"', '"unterminated']),
)


def array_strategy(child):
    return st.lists(
        st.one_of(child, child, child, child, child),
        min_size=0,
        max_size=4,
    ).map(lambda values: "[" + ", ".join(values) + "]")


def inline_strategy(child):
    pairs = st.lists(
        st.tuples(simple_key(), child).map(
            lambda pair: pair[0] + " = " + pair[1]
        ),
        min_size=0,
        max_size=4,
    )
    normal = pairs.map(lambda values: "{ " + ", ".join(values) + " }")
    trailing = pairs.map(
        lambda values: (
            "{ " + ", ".join(values) + (", " if values else "") + " }"
        )
    )
    return st.one_of(normal, trailing)


value_strategy = st.recursive(
    scalar_value,
    lambda child: st.one_of(
        array_strategy(child),
        array_strategy(child),
        inline_strategy(child),
        inline_strategy(child),
    ),
    max_leaves=32,
)


@composite
def assignment(draw):
    return draw(key()) + " = " + draw(value_strategy)


@composite
def assignment_with_comment(draw):
    return draw(key()) + " = " + draw(value_strategy) + " # comment"


@composite
def duplicate_inline(draw):
    name = draw(simple_key())
    first = draw(value_strategy)
    second = draw(value_strategy)
    return "{ " + name + " = " + first + ", " + name + " = " + second + ", }"


@composite
def duplicate_assignment(draw):
    name = draw(simple_key())
    first = draw(value_strategy)
    second = draw(value_strategy)
    return name + " = " + first + "\n" + name + " = " + second


@composite
def table_header(draw):
    return "[" + draw(key()) + "]"


@composite
def array_table_header(draw):
    return "[[" + draw(key()) + "]]"


@composite
def normal_document(draw):
    lines = draw(
        st.lists(
            st.one_of(
                assignment(),
                assignment(),
                assignment_with_comment(),
                duplicate_assignment(),
                table_header(),
                array_table_header(),
            ),
            min_size=1,
            max_size=12,
        )
    )
    return "\n".join(lines)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=50000, max_value=70000))
    leaf = draw(
        st.sampled_from(
            ["0", "nan", "9223372036854775808", '"\\u03bb"']
        )
    )
    if draw(st.booleans()):
        opening = "[" * depth
        closing = "]" * depth
    else:
        opening = "[ " * depth
        closing = " ]" * depth
    return "deep = " + opening + leaf + closing


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=35000, max_value=55000))
    leaf = draw(st.sampled_from(["0", "inf", "true", '"\\u03bb"']))
    quoted = draw(st.booleans())
    value = leaf
    for index in range(depth):
        if quoted:
            name = '"quoted key"' if index % 2 else '"a"'
        else:
            name = "a" if index % 2 else "b"
        value = "{ " + name + " = " + value + " }"
    return "deep = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=50000, max_value=70000))
    quoted = draw(st.booleans())
    names = []
    for index in range(depth):
        if quoted:
            names.append('"a"' if index % 2 == 0 else '"quoted key"')
        else:
            names.append("a" if index % 2 == 0 else "b")
    return ".".join(names) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=35000, max_value=50000))
    value = draw(st.sampled_from(["0", "1", "true", '"x"', "nan"]))
    return "\n".join(
        "key" + str(index) + " = " + value
        for index in range(count)
    )


malformed_document = st.one_of(
    st.just(""),
    st.just("x 1"),
    st.just("x = ["),
    st.just('x = "unterminated'),
    st.just("x = { a = 1\nb = 2 }"),
    st.just("x = [1, 2,]"),
    st.just("x = { a = 1, b = 2, }"),
    st.just("[broken"),
    st.just("[[broken]]\ny = 1"),
    st.just("x = '''unterminated\n"),
)

toml_strategy = st.one_of(
    *([normal_document()] * 20),
    duplicate_inline().map(lambda value: "x = " + value),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    malformed_document,
)