"""Generated strategy - iteration 1, attempt 1.
accepted: False
generated: 2026-09-03T13:03:46.044643+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()\""
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?-_:;()/"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?-_:;()/\""


unicode_escape = st.sampled_from([
    "\\u0000", "\\u0001", "\\u0020", "\\u0041", "\\u00e9",
    "\\u03bb", "\\u20ac", "\\u2603", "\\u2764",
    "\\U00000041", "\\U0001f600", "\\U0001f642",
])

escape_sequence = st.one_of(
    st.sampled_from(["\\n", "\\t", "\\r", "\\b", "\\f", "\\\"", "\\\\", "\\/"]),
    unicode_escape,
)


@composite
def basic_string(draw):
    ordinary = draw(
        st.text(
            alphabet=BASIC_SAFE,
            min_size=0,
            max_size=24,
        )
    )
    escaped = draw(st.lists(escape_sequence, min_size=0, max_size=7))
    pieces = draw(st.permutations([ordinary] + escaped))
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    content = draw(
        st.text(
            alphabet=LITERAL_SAFE,
            min_size=0,
            max_size=28,
        )
    )
    return "'" + content + "'"


@composite
def multiline_basic(draw):
    content = draw(
        st.text(
            alphabet=ML_BASIC_SAFE,
            min_size=0,
            max_size=48,
        )
    )
    return '"""' + content + '"""'


@composite
def multiline_literal(draw):
    content = draw(
        st.text(
            alphabet=ML_LITERAL_SAFE,
            min_size=0,
            max_size=48,
        )
    )
    return "'''" + content + "'''"



def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.one_of(
        basic_string(),
        literal_string(),
    )


def simple_key():
    return st.one_of(unquoted_key(), quoted_key())


@composite
def key(draw):
    first = draw(simple_key())
    rest = draw(st.lists(simple_key(), min_size=0, max_size=3))
    return ".".join([first] + rest)


decimal_digits = st.one_of(
    st.integers(min_value=0, max_value=999999).map(str),
    st.sampled_from([
        "0", "-0", "1", "-1", "007", "00042",
        "9223372036854775807", "-9223372036854775808",
        "9223372036854775808", "-9223372036854775809",
        "1_000", "9_223_372_036_854_775_807",
        "0_0", "12_34_567",
    ]),
)

integer_value = st.one_of(
    decimal_digits,
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
    st.sampled_from([
        "0.0", "-0.0", "1.0", "-1.5", "3.1415926535",
        "1e0", "-1E+10", "6.02e23", "1_000.5", "9.9e-9",
        "inf", "+inf", "-inf", "nan", "+nan", "-nan",
    ]),
    st.tuples(
        st.integers(-999999, 999999).map(str),
        st.integers(0, 999999).map(lambda n: f"{n:06d}"),
        st.integers(-30, 30).map(lambda n: f"{n:+d}"),
    ).map(lambda x: f"{x[0]}.{x[1]}e{x[2]}"),
    st.tuples(
        st.integers(0, 999999).map(str),
        st.integers(1, 999999).map(lambda n: f"{n:06d}"),
    ).map(lambda x: f"{x[0]}.{x[1]}"),
)

date_parts = st.tuples(
    st.integers(1970, 2100).map(lambda n: f"{n:04d}"),
    st.integers(1, 12).map(lambda n: f"{n:02d}"),
    st.integers(1, 28).map(lambda n: f"{n:02d}"),
)

time_parts = st.tuples(
    st.integers(0, 23).map(lambda n: f"{n:02d}"),
    st.integers(0, 59).map(lambda n: f"{n:02d}"),
    st.integers(0, 59).map(lambda n: f"{n:02d}"),
)

offset_value = st.one_of(
    st.just("Z"),
    st.tuples(
        st.sampled_from(["+", "-"]),
        st.integers(0, 23).map(lambda n: f"{n:02d}"),
        st.integers(0, 59).map(lambda n: f"{n:02d}"),
    ).map(lambda x: x[0] + x[1] + ":" + x[2]),
)

date_value = st.one_of(
    date_parts.map(lambda x: f"{x[0]}-{x[1]}-{x[2]}"),
    st.tuples(date_parts, time_parts).map(
        lambda x: f"{x[0][0]}-{x[0][1]}-{x[0][2]}T"
                  f"{x[1][0]}:{x[1][1]}:{x[1][2]}"
    ),
    st.tuples(date_parts, time_parts, offset_value).map(
        lambda x: f"{x[0][0]}-{x[0][1]}-{x[0][2]}T"
                  f"{x[1][0]}:{x[1][1]}:{x[1][2]}{x[2]}"
    ),
    st.tuples(date_parts, time_parts).map(
        lambda x: f"{x[0][0]}-{x[0][1]}-{x[0][2]} "
                  f"{x[1][0]}:{x[1][1]}:{x[1][2]}"
    ),
    st.tuples(
        date_parts,
        time_parts,
        st.integers(0, 9999999999999999999).map(lambda n: f"{n:019d}"),
        offset_value,
    ).map(
        lambda x: f"{x[0][0]}-{x[0][1]}-{x[0][2]}T"
                  f"{x[1][0]}:{x[1][1]}:{x[1][2]}.{x[2]}{x[3]}"
    ),
    st.tuples(
        time_parts,
        st.integers(0, 9999999999999999999).map(lambda n: f"{n:019d}"),
    ).map(
        lambda x: f"{x[0][0]}:{x[0][1]}:{x[0][2]}.{x[1]}"
    ),
    time_parts.map(lambda x: f"{x[0]}:{x[1]}:{x[2]}"),
)


scalar_value = st.one_of(
    basic_string(),
    basic_string(),
    literal_string(),
    multiline_basic(),
    multiline_literal(),
    multiline_literal(),
    integer_value,
    float_value,
    float_value,
    st.sampled_from(["true", "false"]),
    date_value,
    st.sampled_from(['"\\q"', '"\\x"', '"\\uD800"', '"unterminated']),
)


def array_strategy(child):
    elements = st.lists(child, min_size=0, max_size=4)
    return elements.map(lambda xs: "[" + ", ".join(xs) + "]")


def inline_strategy(child):
    pairs = st.lists(
        st.tuples(simple_key(), child).map(
            lambda p: p[0] + " = " + p[1]
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
    depth = draw(st.integers(min_value=48750, max_value=56000))
    leaf = draw(st.one_of(
        integer_value,
        float_value,
        basic_string(),
        multiline_literal(),
        st.just("true"),
    ))
    opening = "".join("[ " if i % 2 else "[" for i in range(depth))
    closing = "".join(" ]" if i % 2 else "]" for i in range(depth - 1, -1, -1))
    return "deep = " + opening + leaf + closing


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=36000))
    value = draw(st.one_of(
        basic_string(),
        multiline_literal(),
        float_value,
        st.just("true"),
    ))
    for i in range(depth):
        name = "a" if i % 2 == 0 else '"quoted key"'
        separator = " = " if i % 3 else "= "
        value = "{ " + name + separator + value + " }"
    return "deep = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=40000, max_value=56000))
    quoted = draw(st.booleans())
    if quoted:
        names = [
            '"a"' if i % 2 == 0 else '"quoted key"'
            for i in range(depth)
        ]
    else:
        names = [
            "a" if i % 3 == 0 else ("b" if i % 3 == 1 else "c")
            for i in range(depth)
        ]
    value = draw(st.one_of(integer_value, float_value, basic_string()))
    return ".".join(names) + " = " + value


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=28000, max_value=38000))
    values = draw(
        st.lists(
            st.one_of(
                st.just("0"),
                st.just("1"),
                st.just("true"),
                basic_string(),
                float_value,
            ),
            min_size=count,
            max_size=count,
        )
    )
    lines = [
        "k" + str(i) + " = " + values[i]
        for i in range(count)
    ]
    return "\n".join(lines)


malformed_document = st.one_of(
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
    duplicate_inline().map(lambda v: "x = " + v),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    malformed_document,
)