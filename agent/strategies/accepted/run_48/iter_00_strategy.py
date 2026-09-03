"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-03T13:01:43.474086+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()\""
HEX = "0123456789abcdefABCDEF"


@composite
def basic_string(draw):
    ordinary = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=24))
    escaped = draw(
        st.lists(
            st.sampled_from(["\\n", "\\t", "\\r", "\\b", "\\f", "\\\"", "\\\\",
                             "\\/", "\\u0000", "\\u0041", "\\u03bb", "\\U0001f600"]),
            min_size=0,
            max_size=5,
        )
    )
    pieces = draw(st.permutations([ordinary] + escaped))
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    return "'" + draw(st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=28)) + "'"


@composite
def multiline_basic(draw):
    content = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?",
            min_size=0,
            max_size=48,
        )
    )
    return '"""' + content + '"""'


@composite
def multiline_literal(draw):
    content = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?\"",
            min_size=0,
            max_size=48,
        )
    )
    return "'''" + content + "'''"



def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()",
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
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda n: "0x" + format(n, "x")),
    st.integers(min_value=0, max_value=0o777777777).map(lambda n: "0o" + format(n, "o")),
    st.integers(min_value=0, max_value=0b111111111).map(lambda n: "0b" + format(n, "b")),
)

float_value = st.one_of(
    st.sampled_from([
        "0.0", "-0.0", "1.0", "-1.5", "3.1415926535",
        "1e0", "-1E+10", "6.02e23", "1_000.5", "9.9e-9",
        "inf", "+inf", "-inf", "nan", "+nan", "-nan",
    ]),
    st.tuples(
        st.integers(-999999, 999999),
        st.integers(0, 999999),
        st.integers(-30, 30),
    ).map(lambda x: f"{x[0]}.{x[1]:06d}e{x[2]:+d}"),
)

date_value = st.one_of(
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}T{x[3]:02d}:{x[4]:02d}:{x[5]:02d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
    ).map(
        lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d} "
                  f"{x[3]:02d}:{x[4]:02d}:{x[5]:02d}.{x[6]:019d}"
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda x: f"{x[0]:02d}:{x[1]:02d}:{x[2]:02d}"),
)


scalar_value = st.one_of(
    basic_string(),
    literal_string(),
    multiline_basic(),
    multiline_literal(),
    integer_value,
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
        st.tuples(simple_key(), child).map(lambda p: p[0] + " = " + p[1]),
        min_size=0,
        max_size=4,
    )
    normal = pairs.map(lambda xs: "{" + ", ".join(xs) + "}")
    trailing = pairs.map(lambda xs: "{" + ", ".join(xs) + (", " if xs else "") + "}")
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
    return draw(key()).join([]) if False else "[" + draw(key()) + "]"


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
            min_size=0,
            max_size=12,
        )
    )
    return "\n".join(lines)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48000, max_value=52000))
    leaf = draw(st.sampled_from(["0", "9223372036854775808", '"😀"', "nan"]))
    return "deep = " + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=12000, max_value=24000))
    value = draw(st.sampled_from(["0", '"😀"', "inf", "true"]))
    for i in range(depth):
        name = "a" if i % 2 == 0 else '"quoted key"'
        value = "{ " + name + " = " + value + " }"
    return "deep = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=12000, max_value=24000))
    quoted = draw(st.booleans())
    if quoted:
        names = ['"a"' if i % 2 == 0 else '"quoted key"' for i in range(depth)]
    else:
        names = ["a" if i % 2 == 0 else "b" for i in range(depth)]
    return ".".join(names) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=2000, max_value=10000))
    value = draw(st.sampled_from(["0", "1", '"x"', "true"]))
    lines = ["k" + str(i) + " = " + value for i in range(count)]
    return "\n".join(lines)


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
    duplicate_inline().map(lambda v: "x = " + v),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    malformed_document,
)