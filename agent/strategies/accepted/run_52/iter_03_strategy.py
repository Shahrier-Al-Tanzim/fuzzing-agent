"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-09-03T17:04:43.515181+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
KEY_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
).replace('"', "").replace("\\", "").replace("\n", "").replace("\r", "")
BASIC_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
).replace('"', "").replace("\\", "").replace("\n", "").replace("\r", "")
LITERAL_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
).replace("'", "").replace("\n", "").replace("\r", "")
ML_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "_-./:!?@#$%^&*()+={}[];,<>|~"
)


@composite
def key(draw):
    unquoted = st.text(
        alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=16
    )
    basic = st.text(
        alphabet=KEY_BODY_CHARS, min_size=0, max_size=16
    ).map(lambda s: '"' + s + '"')
    literal = st.text(
        alphabet=LITERAL_BODY_CHARS, min_size=0, max_size=16
    ).map(lambda s: "'" + s + "'")
    first = draw(st.one_of(unquoted, basic, literal))
    rest = draw(
        st.lists(
            st.one_of(unquoted, basic, literal),
            min_size=0,
            max_size=6,
        )
    )
    return ".".join([first] + rest)


basic_string = st.one_of(
    st.text(
        alphabet=BASIC_BODY_CHARS, min_size=0, max_size=32
    ).map(lambda s: '"' + s + '"'),
    st.tuples(
        st.text(
            alphabet=BASIC_BODY_CHARS, min_size=0, max_size=12
        ),
        st.sampled_from(
            [
                "\\n",
                "\\t",
                "\\r",
                "\\b",
                "\\f",
                '\\"',
                "\\\\",
                "\\/",
                "\\u0000",
                "\\u0041",
                "\\u03a9",
                "\\U0001f9ea",
            ]
        ),
        st.text(
            alphabet=BASIC_BODY_CHARS, min_size=0, max_size=12
        ),
    ).map(lambda p: '"' + p[0] + p[1] + p[2] + '"'),
    st.sampled_from(
        [
            '"\\u0000"',
            '"\\u0041"',
            '"\\u03a9"',
            '"\\uabCd"',
            '"😀"',
            '"𐀀"',
            '"🧪"',
        ]
    ),
)

literal_string = st.one_of(
    st.text(
        alphabet=LITERAL_BODY_CHARS, min_size=0, max_size=32
    ).map(lambda s: "'" + s + "'"),
    st.sampled_from(
        [
            "'literal 😀 𐀀'",
            "'plain literal'",
            "''",
            "'quotes \" are literal'",
        ]
    ),
)

ml_basic_string = st.one_of(
    st.text(
        alphabet=ML_CHARS + "\n",
        min_size=0,
        max_size=64,
    ).map(lambda s: '"""' + s + '"""'),
    st.sampled_from(
        [
            '"""line one\nline two\n"""',
            '"""unicode 😀 𐀀"""',
            '""""""',
            '"""escaped line\\\ncontinuation"""',
            '"""quotes " and backslashes \\\\"""',
        ]
    ),
)

ml_literal_string = st.one_of(
    st.text(
        alphabet=ML_CHARS + "\n'\"",
        min_size=0,
        max_size=64,
    ).map(lambda s: "'''" + s + "'''"),
    st.sampled_from(
        [
            "'''line one\nline two'''",
            "''''''",
            "'''literal \" and ' text'''",
            "'''many\nliteral\nlines'''",
        ]
    ),
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
            "18446744073709551616",
            "-18446744073709551616",
            "007",
            "00",
            "0001",
            "1_000",
            "9_223_372_036_854_775_807",
            "9_223_372_036_854_775_808",
        ]
    ),
    st.tuples(
        st.sampled_from(["", "+", "-"]),
        st.integers(min_value=0, max_value=999999999).map(str),
    ).map(lambda p: p[0] + p[1]),
    st.tuples(
        st.sampled_from(["1", "2", "7", "9"]),
        st.lists(
            st.sampled_from(list("0123456789")),
            min_size=1,
            max_size=12,
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
            "0xffffffffffffffff",
            "0xFFFFFFFFFFFFFFFFFFFFFFFF",
        ]
    ),
    st.tuples(
        st.sampled_from(["0x", "0X"]),
        st.text(
            alphabet="0123456789abcdefABCDEF",
            min_size=1,
            max_size=24,
        ),
    ).map(lambda p: p[0] + p[1]),
)

oct_int = st.one_of(
    st.sampled_from(
        [
            "0o0",
            "0o7",
            "0o755",
            "0o777_777",
            "0o777777777777777777",
        ]
    ),
    st.tuples(
        st.just("0o"),
        st.text(alphabet="01234567", min_size=1, max_size=20),
    ).map(lambda p: p[0] + p[1]),
)

bin_int = st.one_of(
    st.sampled_from(
        [
            "0b0",
            "0b1",
            "0b1010",
            "0b1111_0000",
            "0b" + "1" * 64,
        ]
    ),
    st.tuples(
        st.just("0b"),
        st.text(alphabet="01", min_size=1, max_size=32),
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
            "1e-300",
            "inf",
            "+inf",
            "-inf",
            "nan",
            "+nan",
            "-nan",
        ]
    ),
    st.tuples(
        st.integers(min_value=0, max_value=999999).map(str),
        st.integers(min_value=0, max_value=999999999).map(str),
    ).map(lambda p: p[0] + "." + p[1]),
    st.tuples(
        st.integers(min_value=0, max_value=999999).map(str),
        st.integers(min_value=0, max_value=999999).map(str),
        st.sampled_from(["e", "E"]),
        st.sampled_from(["", "+", "-"]),
        st.integers(min_value=0, max_value=9999).map(str),
    ).map(lambda p: p[0] + "." + p[1] + p[2] + p[3] + p[4]),
)

date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2199),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999999999999999),
    ).map(
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}T"
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}.{p[6]:021d}Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2199),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999999999999999),
        st.sampled_from(["+", "-"]),
        st.integers(0, 23),
        st.integers(0, 59),
    ).map(
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d} "
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}.{p[6]:021d}"
            f"{p[7]}{p[8]:02d}:{p[9]:02d}"
        )
    ),
    st.tuples(
        st.integers(1970, 2199),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda p: f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999999999999999),
    ).map(
        lambda p: (
            f"{p[0]:02d}:{p[1]:02d}:{p[2]:02d}.{p[3]:021d}"
        )
    ),
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
            lambda xs: (
                "{"
                + ", ".join(p[0] + " = " + p[1] for p in xs)
                + "}"
            )
        ),
        st.lists(
            st.tuples(key(), child),
            min_size=1,
            max_size=4,
        ).map(
            lambda xs: (
                "{"
                + ", ".join(p[0] + " = " + p[1] for p in xs)
                + ",}"
            )
        ),
        st.lists(child, min_size=1, max_size=4).map(
            lambda xs: "[\n" + ",\n".join(xs) + ",\n]"
        ),
    ),
    max_leaves=64,
)

biased_value = st.recursive(
    scalar,
    lambda child: st.one_of(
        child,
        child,
        child,
        st.lists(
            st.one_of(child, child, child, child),
            min_size=1,
            max_size=2,
        ).map(lambda xs: "[" + ",".join(xs) + "]"),
        st.lists(
            st.one_of(child, child, child, child),
            min_size=1,
            max_size=2,
        ).map(lambda xs: "[" + ",".join(xs) + "]"),
        st.lists(
            st.tuples(key(), child),
            min_size=1,
            max_size=2,
        ).map(
            lambda xs: (
                "{"
                + ",".join(p[0] + "=" + p[1] for p in xs)
                + "}"
            )
        ),
    ),
    max_leaves=96,
)

pair = st.tuples(key(), value).map(
    lambda p: p[0] + " = " + p[1]
)
biased_pair = st.tuples(key(), biased_value).map(
    lambda p: p[0] + " = " + p[1]
)

comment_text = st.text(
    alphabet=BASIC_BODY_CHARS + " ",
    min_size=0,
    max_size=24,
).map(lambda s: " # " + s)


@composite
def normal_document(draw):
    kind = draw(st.integers(min_value=0, max_value=11))
    if kind <= 5:
        lines = draw(st.lists(pair, min_size=1, max_size=10))
        return "\n".join(lines)
    if kind == 6:
        lines = draw(
            st.lists(
                st.tuples(pair, comment_text),
                min_size=1,
                max_size=8,
            )
        )
        return "\n".join(p[0] + p[1] for p in lines)
    if kind == 7:
        header = draw(key())
        lines = draw(st.lists(pair, min_size=1, max_size=8))
        return "[" + header + "]\n" + "\n".join(lines)
    if kind == 8:
        header = draw(key())
        lines = draw(st.lists(pair, min_size=1, max_size=8))
        return "[[" + header + "]]\n" + "\n".join(lines)
    if kind == 9:
        first = draw(pair)
        second = draw(pair)
        return first + "\n" + second
    if kind == 10:
        lines = draw(st.lists(biased_pair, min_size=1, max_size=5))
        return "\n".join(lines)
    header = draw(key())
    lines = draw(st.lists(pair, min_size=1, max_size=5))
    return "[" + header + "]\n" + "\n".join(lines)


@composite
def duplicate_document(draw):
    repeated = draw(key())
    first = draw(value)
    second = draw(value)
    return (
        repeated
        + " = "
        + first
        + "\n"
        + repeated
        + " = "
        + second
    )


@composite
def trailing_inline_document(draw):
    first = draw(value)
    second = draw(value)
    return "x = {a = " + first + ", b = " + second + ",}"


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=49001, max_value=72000))
    style = draw(st.integers(min_value=0, max_value=4))
    if style == 0:
        opens = "[" * depth
    elif style == 1:
        opens = "[\n" * depth
    elif style == 2:
        opens = "[ " * depth
    elif style == 3:
        opens = "".join(
            "[\n" if i % 2 else "[ " for i in range(depth)
        )
    else:
        opens = "".join(
            "[\n" if i % 3 == 0 else "[ " if i % 3 == 1 else "["
            for i in range(depth)
        )
    return "deep = " + opens + "0" + "]" * depth


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=40001, max_value=68000))
    style = draw(st.integers(min_value=0, max_value=3))
    if style == 0:
        pieces = ["{a="] * depth
    elif style == 1:
        pieces = [
            '{"q"=' if i % 2 else "{a=" for i in range(depth)
        ]
    elif style == 2:
        pieces = [
            "'q'=" if False else (
                "{'q'=" if i % 3 == 0
                else '{"v"=' if i % 3 == 1
                else "{a="
            )
            for i in range(depth)
        ]
    else:
        pieces = [
            '{"quoted-key"=' if i % 2 else "{a="
            for i in range(depth)
        ]
    return "deep = " + "".join(pieces) + "0" + "}" * depth


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=40001, max_value=72000))
    style = draw(st.integers(min_value=0, max_value=3))
    if style == 0:
        pieces = ["a"] * depth
    elif style == 1:
        pieces = ['"q"' if i % 2 else "a" for i in range(depth)]
    elif style == 2:
        pieces = [
            "'q'" if i % 3 == 0
            else '"v"' if i % 3 == 1
            else "a"
            for i in range(depth)
        ]
    else:
        pieces = [
            '"quoted key"' if i % 2 else "segment"
            for i in range(depth)
        ]
    return ".".join(pieces) + " = 0"


@composite
def many_sibling_document(draw):
    count = draw(st.integers(min_value=30001, max_value=52000))
    style = draw(st.integers(min_value=0, max_value=3))
    lines = ["[large]"]
    for i in range(count):
        if style == 0:
            name = "k" + str(i)
        elif style == 1:
            name = '"k' + str(i) + '"'
        elif style == 2:
            name = "group" + str(i % 17) + ".k" + str(i)
        else:
            name = "'item" + str(i) + "'"
        lines.append(name + " = " + ("0" if i % 5 else "true"))
    return "\n".join(lines)


@composite
def long_document(draw):
    count = draw(st.integers(min_value=18000, max_value=42000))
    style = draw(st.integers(min_value=0, max_value=2))
    lines = []
    for i in range(count):
        if style == 0:
            name = "line" + str(i)
        elif style == 1:
            name = "section" + str(i % 31) + ".value" + str(i)
        else:
            name = '"line ' + str(i) + '"'
        lines.append(name + " = " + ("false" if i % 7 else "1"))
    return "\n".join(lines)


@composite
def special_document(draw):
    kind = draw(st.integers(min_value=0, max_value=5))
    if kind == 0:
        return "multiline = " + draw(ml_basic_string)
    if kind == 1:
        return "literal_multiline = " + draw(ml_literal_string)
    if kind == 2:
        return "hex_value = " + draw(hex_int)
    if kind == 3:
        return "oct_value = " + draw(oct_int)
    if kind == 4:
        return "binary_value = " + draw(bin_int)
    header = draw(key())
    body = draw(
        st.lists(pair, min_size=1, max_size=4)
    )
    return "[[" + header + "]]\n" + "\n".join(body)


toml_strategy = st.one_of(
    *([normal_document()] * 20),
    duplicate_document(),
    trailing_inline_document(),
    special_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_sibling_document(),
    long_document(),
)