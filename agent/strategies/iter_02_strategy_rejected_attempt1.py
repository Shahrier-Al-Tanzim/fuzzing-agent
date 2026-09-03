"""Generated strategy - iteration 2, attempt 1.
accepted: False
generated: 2026-09-03T13:11:24.195086+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():;"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():;\""
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/():;"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/():;\""
HEX = "0123456789abcdefABCDEF"


@composite
def basic_string(draw):
    ordinary = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=24))
    escaped = draw(
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
    pieces = draw(st.permutations([ordinary] + escaped))
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    return "'" + draw(
        st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=28)
    ) + "'"


@composite
def multiline_basic(draw):
    content = draw(st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=48))
    return '"""' + content + '"""'


@composite
def multiline_literal(draw):
    content = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/():;\"",
            min_size=0,
            max_size=48,
        )
    )
    return "'''" + content + "'''"


def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.text(
        alphabet=BASIC_SAFE,
        min_size=1,
        max_size=12,
    ).map(lambda s: '"' + s + '"')


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
        lambda n: "0x" + format(n, "x")
    ),
    st.integers(min_value=0, max_value=0o777777777).map(
        lambda n: "0o" + format(n, "o")
    ),
    st.integers(min_value=0, max_value=0b111111111).map(
        lambda n: "0b" + format(n, "b")
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
            lambda n: f"{n:06d}"
        ),
        st.integers(min_value=-30, max_value=30),
    ).map(lambda pair: f"{pair[0]}.{pair[1]}e{pair[2]:+d}"),
    st.tuples(
        valid_decimal,
        st.integers(min_value=1, max_value=999999).map(
            lambda n: f"{n:06d}"
        ),
    ).map(lambda pair: f"{pair[0]}.{pair[1]}"),
)

date_value = st.one_of(
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
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T"
        f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
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
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} "
        f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:019d}"
        f"{t[7]:+03d}:{t[8]:02d}"
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
)

scalar_value = st.one_of(
    st.just("0"),
    st.just("1"),
    st.just("true"),
    st.just("false"),
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
    ).map(lambda xs: "[" + ", ".join(xs) + "]")


def inline_strategy(child):
    pairs = st.lists(
        st.tuples(simple_key(), child).map(
            lambda pair: pair[0] + " = " + pair[1]
        ),
        min_size=0,
        max_size=4,
    )
    normal = pairs.map(lambda xs: "{" + ", ".join(xs) + "}")
    trailing = pairs.map(
        lambda xs: "{" + ", ".join(xs) + (", " if xs else "") + "}"
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
def duplicate_inline(draw):
    k = draw(simple_key())
    a = draw(value_strategy)
    b = draw(value_strategy)
    return "{ " + k + " = " + a + ", " + k + " = " + b + ", }"


@composite
def duplicate_assignment(draw):
    k = draw(simple_key())
    a = draw(value_strategy)
    b = draw(value_strategy)
    return k + " = " + a + "\n" + k + " = " + b


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
                assignment(),
                table_header(),
                array_table_header(),
            ),
            min_size=1,
            max_size=12,
        )
    )
    return "\n".join(lines)


unicode_assignment = st.tuples(
    key(),
    st.sampled_from(
        [
            '"\\u0000"',
            '"\\u0041"',
            '"\\u03bb"',
            '"\\U0001f600"',
            '"prefix\\n\\t\\u03bb"',
        ]
    ),
).map(lambda pair: pair[0] + " = " + pair[1])

nan_assignment = st.tuples(
    key(),
    st.sampled_from(["nan", "+nan", "-nan"]),
).map(lambda pair: pair[0] + " = " + pair[1])

overflow_assignment = st.tuples(
    key(),
    st.sampled_from(
        [
            "9223372036854775808",
            "-9223372036854775809",
            "9_223_372_036_854_775_808",
            "-9_223_372_036_854_775_809",
        ]
    ),
).map(lambda pair: pair[0] + " = " + pair[1])

leading_zero_assignment = st.tuples(
    key(),
    st.sampled_from(["00", "007", "00042", "012_345", "0_0"]),
).map(lambda pair: pair[0] + " = " + pair[1])

commented_assignment = assignment().map(
    lambda line: line + " # generated comment"
)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=52000, max_value=56000))
    leaf = draw(st.sampled_from(["0", "nan", "9223372036854775808", '"\\u03bb"']))
    openings = "".join("[" if i % 2 else "[ " for i in range(depth))
    closings = "".join("]" if i % 2 else " ]" for i in range(depth))
    return "deep = " + openings + leaf + closings


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=28000, max_value=34000))
    leaf = draw(st.sampled_from(["0", "inf", "true", '"\\u03bb"']))
    quoted = draw(st.booleans())
    value = leaf
    for i in range(depth):
        if quoted:
            name = '"quoted key"' if i % 2 else '"a"'
        else:
            name = "a" if i % 2 else "b"
        value = "{ " + name + " = " + value + " }"
    return "deep = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=38000, max_value=46000))
    quoted = draw(st.booleans())
    names = []
    for i in range(depth):
        if quoted:
            names.append('"a"' if i % 2 == 0 else '"quoted key"')
        else:
            names.append("a" if i % 2 == 0 else "b")
    return ".".join(names) + " = " + draw(
        st.sampled_from(["0", "nan", "9223372036854775808"])
    )


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=22000, max_value=28000))
    value = draw(st.sampled_from(["0", "1", '"x"', "true", "nan"]))
    return "\n".join(
        "k" + str(i) + " = " + value for i in range(count)
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
    unicode_assignment,
    nan_assignment,
    overflow_assignment,
    leading_zero_assignment,
    duplicate_inline().map(lambda value: "x = " + value),
    duplicate_assignment,
    commented_assignment,
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    malformed_document,
)