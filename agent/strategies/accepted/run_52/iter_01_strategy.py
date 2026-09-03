"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-03T16:55:26.491577+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
)
LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
)
ML_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
)


@composite
def key(draw):
    unquoted = st.text(
        alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
    )
    basic = st.text(
        alphabet=BASIC_CHARS, min_size=0, max_size=12
    ).map(lambda s: '"' + s + '"')
    literal = st.text(
        alphabet=LITERAL_CHARS, min_size=0, max_size=12
    ).map(lambda s: "'" + s + "'")
    simple = draw(st.one_of(unquoted, basic, literal))
    rest = draw(
        st.lists(
            st.one_of(unquoted, basic, literal),
            min_size=0,
            max_size=4,
        )
    )
    return ".".join([simple] + rest)


basic_string = st.one_of(
    st.text(alphabet=BASIC_CHARS, min_size=0, max_size=24).map(
        lambda s: '"' + s + '"'
    ),
    st.tuples(
        st.text(alphabet=BASIC_CHARS, min_size=0, max_size=8),
        st.sampled_from(
            ["\\n", "\\t", "\\r", "\\b", "\\f", '\\"', "\\\\", "\\/", "\\u0041"]
        ),
        st.text(alphabet=BASIC_CHARS, min_size=0, max_size=8),
    ).map(lambda p: '"' + p[0] + p[1] + p[2] + '"'),
    st.sampled_from(
        [
            '"\\u0000"',
            '"\\u0041"',
            '"\\u03a9"',
            '"\\uabcd"',
            '"😀"',
            '"𐀀"',
            '"🧪"',
        ]
    ),
)

literal_string = st.one_of(
    st.text(alphabet=LITERAL_CHARS, min_size=0, max_size=24).map(
        lambda s: "'" + s + "'"
    ),
    st.sampled_from(["'literal 😀 𐀀'", "'plain literal'"]),
)

ml_basic_string = st.one_of(
    st.text(alphabet=ML_CHARS + "\n", min_size=0, max_size=40).map(
        lambda s: '"""' + s + '"""'
    ),
    st.sampled_from(
        [
            '"""line one\nline two\n"""',
            '"""unicode 😀 𐀀"""',
            '""""""',
        ]
    ),
)

ml_literal_string = st.one_of(
    st.text(
        alphabet=ML_CHARS + "\n'\"",
        min_size=0,
        max_size=40,
    ).map(lambda s: "'''" + s + "'''"),
    st.sampled_from(["'''line one\nline two'''", "''''''"]),
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
    ).map(lambda p: p[0] + p[1]),
    st.tuples(
        st.sampled_from(["1", "2", "7", "9"]),
        st.lists(
            st.sampled_from(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]),
            min_size=1,
            max_size=8,
        ),
    ).map(lambda p: p[0] + "_" + "_".join(p[1])),
)

hex_int = st.one_of(
    st.sampled_from(
        [
            "0x0",
            "0x1",
            "0x7f",
            "0x8000000000000000",
            "0xFFFF_FFFF",
            "0xdead_beef",
        ]
    ),
    st.tuples(
        st.sampled_from(["0x", "0X"]),
        st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=16),
    ).map(lambda p: p[0] + p[1]),
)

oct_int = st.one_of(
    st.sampled_from(["0o0", "0o7", "0o755", "0o777_777"]),
    st.tuples(
        st.just("0o"),
        st.text(alphabet="01234567", min_size=1, max_size=12),
    ).map(lambda p: p[0] + p[1]),
)

bin_int = st.one_of(
    st.sampled_from(["0b0", "0b1", "0b1010", "0b1111_0000"]),
    st.tuples(
        st.just("0b"),
        st.text(alphabet="01", min_size=1, max_size=16),
    ).map(lambda p: p[0] + p[1]),
)

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
    ).map(lambda p: p[0] + "." + p[1]),
    st.tuples(
        st.integers(min_value=0, max_value=9999).map(str),
        st.integers(min_value=0, max_value=9999).map(str),
        st.sampled_from(["e", "E"]),
        st.sampled_from(["", "+", "-"]),
        st.integers(min_value=0, max_value=999).map(str),
    ).map(lambda p: p[0] + "." + p[1] + p[2] + p[3] + p[4]),
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
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}T"
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}.{p[6]:09d}Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999),
        st.sampled_from(["+", "-"]),
        st.integers(0, 23),
        st.integers(0, 59),
    ).map(
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d} "
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}.{p[6]:09d}"
            f"{p[7]}{p[8]:02d}:{p[9]:02d}"
        )
    ),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda p: f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999),
    ).map(lambda p: f"{p[0]:02d}:{p[1]:02d}:{p[2]:02d}.{p[3]:09d}"),
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
            + ", ".join(p[0] + " = " + p[1] for p in xs)
            + "}"
        ),
        st.lists(
            st.tuples(key(), child),
            min_size=1,
            max_size=4,
        ).map(
            lambda xs: "{"
            + ", ".join(p[0] + " = " + p[1] for p in xs)
            + ",}"
        ),
        st.lists(child, min_size=1, max_size=4).map(
            lambda xs: "[\n" + ",\n".join(xs) + ",\n]"
        ),
    ),
    max_leaves=48,
)

biased_value = st.recursive(
    scalar,
    lambda child: st.one_of(
        child,
        child,
        st.lists(child, min_size=1, max_size=2).map(
            lambda xs: "[" + ",".join(xs) + "]"
        ),
        st.lists(child, min_size=1, max_size=2).map(
            lambda xs: "[" + ",".join(xs) + "]"
        ),
        st.lists(
            st.tuples(key(), child),
            min_size=1,
            max_size=2,
        ).map(
            lambda xs: "{"
            + ",".join(p[0] + "=" + p[1] for p in xs)
            + "}"
        ),
    ),
    max_leaves=80,
)

pair = st.tuples(key(), value).map(lambda p: p[0] + " = " + p[1])
biased_pair = st.tuples(key(), biased_value).map(
    lambda p: p[0] + " = " + p[1]
)

comment_text = st.text(
    alphabet=BASIC_CHARS + " ",
    min_size=0,
    max_size=18,
).map(lambda s: " # " + s)


@composite
def normal_document(draw):
    kind = draw(st.integers(min_value=0, max_value=9))
    if kind == 0:
        return ""
    if kind <= 5:
        lines = draw(st.lists(pair, min_size=1, max_size=8))
        return "\n".join(lines)
    if kind == 6:
        lines = draw(
            st.lists(
                st.tuples(pair, comment_text),
                min_size=1,
                max_size=6,
            ).map(lambda xs: [p[0] + p[1] for p in xs])
        )
        return "\n".join(lines)
    if kind == 7:
        header = draw(key())
        lines = draw(st.lists(pair, min_size=1, max_size=6))
        return "[" + header + "]\n" + "\n".join(lines)
    if kind == 8:
        header = draw(key())
        lines = draw(st.lists(pair, min_size=1, max_size=6))
        return "[[" + header + "]]\n" + "\n".join(lines)
    first = draw(pair)
    second = draw(pair)
    return first + "\n" + second


@composite
def biased_document(draw):
    count = draw(st.integers(min_value=1, max_value=4))
    lines = [draw(biased_pair) for _ in range(count)]
    return "\n".join(lines)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=49001, max_value=70000))
    style = draw(st.integers(min_value=0, max_value=2))
    if style == 0:
        opens = "[" * depth
    elif style == 1:
        opens = "[\n" * depth
    else:
        opens = ("[\n" if depth % 2 else "[ ") * depth
    return "deep = " + opens + "0" + "]" * depth


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=33001, max_value=52000))
    style = draw(st.integers(min_value=0, max_value=2))
    parts = []
    for i in range(depth):
        if style == 0:
            parts.append("{a=")
        elif style == 1:
            parts.append('{"q"=' if i % 2 else "{a=")
        else:
            parts.append("'q'=" if False else ('{a=' if i % 3 else '{"v"='))
    return "deep = " + "".join(parts) + "0" + "}" * depth


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=22001, max_value=52000))
    style = draw(st.integers(min_value=0, max_value=2))
    pieces = []
    for i in range(depth):
        if style == 0:
            pieces.append("a")
        elif style == 1:
            pieces.append('"q"' if i % 2 else "a")
        else:
            pieces.append("'q'" if i % 3 else '"v"')
    return ".".join(pieces) + " = 0"


@composite
def long_document(draw):
    count = draw(st.integers(min_value=18001, max_value=40000))
    style = draw(st.integers(min_value=0, max_value=1))
    lines = []
    for i in range(count):
        if style and i % 2:
            name = '"k' + str(i) + '"'
        else:
            name = "k" + str(i)
        lines.append(name + " = 0")
    return "\n".join(lines)


@composite
def deep_biased_document(draw):
    return draw(biased_document())


toml_strategy = st.one_of(
    *([normal_document()] * 20),
    deep_array_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_inline_document(),
    deep_dotted_document(),
    deep_dotted_document(),
    long_document(),
    deep_biased_document(),
)