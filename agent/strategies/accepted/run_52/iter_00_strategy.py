"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-03T16:52:44.500176+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
QUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:!?@#$%^&*()+={}[];,<>|~"
LITERAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:!?@#$%^&*()+={}[];,<>|~"
PLAIN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:!?@#$%^&*()+={}[],<>|~"
HEX = "0123456789abcdefABCDEF"


@composite
def key(draw):
    unquoted = st.text(alphabet=UNQUOTED, min_size=1, max_size=12)
    basic = st.text(alphabet=QUOTED, min_size=0, max_size=12).map(
        lambda s: '"' + s + '"'
    )
    literal = st.text(alphabet=LITERAL, min_size=0, max_size=12).map(
        lambda s: "'" + s + "'"
    )
    simple = draw(st.one_of(unquoted, basic, literal))
    extra = draw(
        st.lists(
            st.one_of(unquoted, basic, literal),
            min_size=0,
            max_size=4,
        )
    )
    if extra:
        return ".".join([simple] + extra)
    return simple


escaped_basic = st.sampled_from(
    [
        '"\\n"',
        '"\\t"',
        '"\\r"',
        '"\\b"',
        '"\\f"',
        '"\\\""',
        '"\\\\"',
        '"\\/"',
        '"\\u0000"',
        '"\\u0041"',
        '"\\u03a9"',
        '"\\uabcd"',
        '"😀"',
        '"𐀀"',
        '"🧪"',
    ]
)

basic_string = st.one_of(
    escaped_basic,
    st.text(alphabet=PLAIN, min_size=0, max_size=20).map(
        lambda s: '"' + s + '"'
    ),
    st.tuples(
        st.text(alphabet=PLAIN, min_size=0, max_size=8),
        st.sampled_from(["\\n", "\\t", "\\\"", "\\\\", "\\u0041"]),
        st.text(alphabet=PLAIN, min_size=0, max_size=8),
    ).map(lambda x: '"' + x[0] + x[1] + x[2] + '"'),
    st.just('"\\q"'),
    st.just('"\\xFF"'),
    st.just('"unterminated'),
)

literal_string = st.one_of(
    st.text(alphabet=LITERAL, min_size=0, max_size=24).map(
        lambda s: "'" + s + "'"
    ),
    st.just("'literal 😀 𐀀'"),
    st.just("'unterminated"),
)

ml_basic_string = st.one_of(
    st.text(alphabet=PLAIN + "\n", min_size=0, max_size=32).map(
        lambda s: '"""' + s + '"""'
    ),
    st.just('"""line one\nline two\n"""'),
    st.just('"""unicode 😀 𐀀"""'),
)

ml_literal_string = st.one_of(
    st.text(alphabet=PLAIN + "\n'\"", min_size=0, max_size=32).map(
        lambda s: "'''" + s + "'''"
    ),
    st.just("'''line one\nline two'''"),
)

decimal_int = st.one_of(
    st.sampled_from(
        [
            "0",
            "-0",
            "+0",
            "1",
            "-1",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "007",
            "00",
            "1_000",
            "9_223_372_036_854_775_807",
        ]
    ),
    st.tuples(
        st.sampled_from(["", "+", "-"]),
        st.integers(min_value=0, max_value=999999).map(str),
    ).map(lambda x: x[0] + x[1]),
)

hex_int = st.sampled_from(
    ["0x0", "0x1", "0x7f", "0x8000000000000000", "0xFFFF_FFFF", "0xdead_beef"]
)
oct_int = st.sampled_from(["0o0", "0o7", "0o755", "0o777_777"])
bin_int = st.sampled_from(["0b0", "0b1", "0b1010", "0b1111_0000"])

floating = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "+0.0",
            "1.5",
            "-3.14159",
            "1e0",
            "1E+10",
            "-2e-9",
            "6.02e23",
            "1_000.000_001",
            "1.0e+308",
            "inf",
            "+inf",
            "-inf",
            "nan",
            "+nan",
            "-nan",
        ]
    ),
    st.tuples(
        st.integers(min_value=0, max_value=9999).map(str),
        st.integers(min_value=0, max_value=999999).map(str),
    ).map(lambda x: x[0] + "." + x[1]),
)

date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999),
    ).map(
        lambda x: (
            f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}T"
            f"{x[3]:02d}:{x[4]:02d}:{x[5]:02d}.{x[6]:09d}Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}"),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999),
    ).map(lambda x: f"{x[0]:02d}:{x[1]:02d}:{x[2]:02d}.{x[3]:09d}"),
    st.sampled_from(
        [
            "1979-05-27T00:32:00.9999999999999999999-07:00",
            "1979-05-27 00:32:00Z",
            "2000-01-01t12:30:59+05:30",
        ]
    ),
)

scalar = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
    decimal_int,
    hex_int,
    oct_int,
    bin_int,
    floating,
    st.sampled_from(["true", "false"]),
    date_time,
)

value = st.recursive(
    scalar,
    lambda child: st.one_of(
        st.lists(child, min_size=0, max_size=4).map(
            lambda xs: "[" + ", ".join(xs) + "]"
        ),
        st.lists(
            st.tuples(key(), child),
            min_size=0,
            max_size=4,
        ).map(
            lambda xs: "{"
            + ", ".join(k + " = " + v for k, v in xs)
            + "}"
        ),
        st.lists(
            st.tuples(key(), child),
            min_size=1,
            max_size=3,
        ).map(
            lambda xs: "{"
            + ", ".join(k + " = " + v for k, v in xs)
            + ",}"
        ),
        st.lists(child, min_size=1, max_size=3).map(
            lambda xs: "[\n" + ",\n".join(xs) + ",\n]"
        ),
    ),
    max_leaves=36,
)

pair = st.tuples(key(), value).map(lambda x: x[0] + " = " + x[1])
pair_with_comment = st.tuples(pair, st.text(alphabet=PLAIN, min_size=0, max_size=12)).map(
    lambda x: x[0] if not x[1] else x[0] + " # " + x[1]
)

table_line = st.one_of(
    key().map(lambda k: "[" + k + "]"),
    key().map(lambda k: "[[" + k + "]]"),
)

normal_document = st.one_of(
    st.just(""),
    st.lists(
        st.one_of(pair, pair_with_comment, table_line),
        min_size=1,
        max_size=8,
    ).map(lambda xs: "\n".join(xs)),
    st.tuples(
        key(),
        value,
        key(),
        value,
    ).map(lambda x: x[0] + " = " + x[1] + "\n" + x[2] + " = " + x[3]),
    st.tuples(key(), value).map(
        lambda x: x[0] + " = " + x[1] + "\n" + x[0] + " = " + x[1]
    ),
    st.tuples(key(), value).map(
        lambda x: x[0] + " = " + x[1] + "\n" + x[0] + " " + x[1]
    ),
    st.tuples(key(), value).map(
        lambda x: x[0] + " = " + x[1] + "\n" + x[0] + " ="
    ),
    st.tuples(key(), value).map(
        lambda x: x[0] + " = " + x[1] + "\n[" + x[0]
    ),
)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48001, max_value=65000))
    style = draw(st.integers(min_value=0, max_value=1))
    if style:
        opens = "[\n" * depth
    else:
        opens = "[" * depth
    return "deep = " + opens + "0" + "]" * depth


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=20001, max_value=32000))
    quoted = draw(st.integers(min_value=0, max_value=1))
    parts = []
    for i in range(depth):
        if quoted and i % 2:
            parts.append('{"q"=')
        else:
            parts.append("{a=")
    return "deep = " + "".join(parts) + "0" + "}" * depth


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=12001, max_value=22000))
    quoted = draw(st.integers(min_value=0, max_value=1))
    pieces = []
    for i in range(depth):
        pieces.append('"q"' if quoted and i % 2 else "a")
    return ".".join(pieces) + " = 0"


@composite
def long_document(draw):
    count = draw(st.integers(min_value=9000, max_value=18000))
    quoted = draw(st.integers(min_value=0, max_value=1))
    lines = []
    for i in range(count):
        name = '"k' + str(i) + '"' if quoted and i % 2 else "k" + str(i)
        lines.append(name + " = 0")
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([normal_document] * 20),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    long_document(),
)