"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-09-02T23:19:02.615746+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE_CHARS = st.characters(
    blacklist_characters="\"\\\n\r",
    blacklist_categories=("Cc",),
)
LITERAL_SAFE_CHARS = st.characters(
    blacklist_characters="'\n\r",
    blacklist_categories=("Cc",),
)


@composite
def quoted_key(draw):
    body = draw(st.text(alphabet=BASIC_SAFE_CHARS, min_size=0, max_size=12))
    return '"' + body + '"'


@composite
def literal_key(draw):
    body = draw(st.text(alphabet=LITERAL_SAFE_CHARS, min_size=0, max_size=12))
    return "'" + body + "'"


simple_key = st.one_of(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12),
    quoted_key(),
    literal_key(),
)


@composite
def key(draw):
    first = draw(simple_key)
    rest = draw(st.lists(simple_key, min_size=0, max_size=3))
    return ".".join([first] + rest)


@composite
def basic_string(draw):
    escaped_unicode = st.integers(min_value=0, max_value=0xFFFF).map(
        lambda n: "\\u%04x" % n
    )
    escapes = st.sampled_from(
        ["\\n", "\\t", "\\r", "\\b", "\\f", '\\"', "\\\\", "\\/", "\\u0000"]
    )
    pieces = draw(
        st.lists(
            st.one_of(
                st.text(alphabet=BASIC_SAFE_CHARS, min_size=1, max_size=8),
                escapes,
                escaped_unicode,
            ),
            min_size=0,
            max_size=8,
        )
    )
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    body = draw(st.text(alphabet=LITERAL_SAFE_CHARS, min_size=0, max_size=32))
    return "'" + body + "'"


@composite
def multiline_basic_string(draw):
    pieces = draw(
        st.lists(
            st.one_of(
                st.text(
                    alphabet=st.characters(
                        blacklist_characters='"\\',
                        blacklist_categories=("Cc",),
                    ),
                    min_size=1,
                    max_size=12,
                ),
                st.sampled_from(["\\\n", "\\\r\n", "\\n", "\\t", '\\"', "\\\\"]),
            ),
            min_size=0,
            max_size=10,
        )
    )
    return '"""' + "".join(pieces) + '"""'


@composite
def multiline_literal_string(draw):
    body = draw(
        st.text(
            alphabet=st.characters(
                blacklist_characters="'",
                blacklist_categories=("Cc",),
            ),
            min_size=0,
            max_size=48,
        )
    )
    return "'''" + body + "'''"


invalid_string = st.sampled_from(
    ['"\\q"', '"\\x"', '"unterminated', "'unterminated", '"""unterminated']
)

string_value = st.one_of(
    basic_string(),
    literal_string(),
    multiline_basic_string(),
    multiline_literal_string(),
    invalid_string,
)


@composite
def decimal_integer(draw):
    return draw(
        st.one_of(
            st.sampled_from(
                [
                    "0",
                    "-0",
                    "1",
                    "-1",
                    "9223372036854775807",
                    "-9223372036854775808",
                    "9223372036854775808",
                    "-9223372036854775809",
                    "007",
                    "-007",
                    "1_000_000",
                    "9_223_372_036_854_775_807",
                ]
            ),
            st.integers(min_value=-1000000, max_value=1000000).map(str),
            st.tuples(
                st.integers(min_value=1, max_value=9),
                st.lists(
                    st.integers(min_value=0, max_value=9).map(str),
                    min_size=1,
                    max_size=12,
                ),
            ).map(lambda p: str(p[0]) + "_" .join(p[1])),
        )
    )


hex_integer = st.tuples(
    st.sampled_from(["0x", "0o", "0b"]),
    st.text(alphabet="0123456789abcdefABCDEF_", min_size=1, max_size=16),
).map(lambda p: p[0] + p[1])

valid_hex = st.integers(min_value=0, max_value=0xFFFFFFFFFFFFFFFF).map(
    lambda n: "0x%x" % n
)
valid_oct = st.integers(min_value=0, max_value=0o77777777777).map(
    lambda n: "0o%o" % n
)
valid_bin = st.integers(min_value=0, max_value=0xFFFF).map(
    lambda n: "0b%b" % n
)

integer_value = st.one_of(decimal_integer(), valid_hex, valid_oct, valid_bin)


@composite
def floating_value(draw):
    mantissa = draw(
        st.one_of(
            st.sampled_from(["0.0", "-0.0", "1.0", "-1.0", "1_000.0"]),
            st.tuples(
                st.integers(min_value=-999999, max_value=999999).map(str),
                st.integers(min_value=0, max_value=999999).map(
                    lambda n: "%06d" % n
                ),
            ).map(lambda p: p[0] + "." + p[1]),
        )
    )
    exponent = draw(
        st.one_of(
            st.just(""),
            st.integers(min_value=-300, max_value=300).map(
                lambda n: "e%+d" % n
            ),
            st.sampled_from(["e10", "E-10", "e1_000"]),
        )
    )
    return mantissa + exponent


@composite
def date_time_value(draw):
    year = draw(st.integers(min_value=0, max_value=9999))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    fraction = draw(
        st.one_of(
            st.just(""),
            st.integers(min_value=0, max_value=9999999999999999999).map(
                lambda n: "." + str(n).zfill(19)
            ),
        )
    )
    zone = draw(
        st.one_of(
            st.just("Z"),
            st.tuples(
                st.sampled_from(["+", "-"]),
                st.integers(min_value=0, max_value=23),
                st.integers(min_value=0, max_value=59),
            ).map(lambda p: "%s%02d:%02d" % (p[0], p[1], p[2])),
        )
    )
    date = "%04d-%02d-%02d" % (year, month, day)
    time = "%02d:%02d:%02d" % (hour, minute, second)
    return draw(
        st.one_of(
            st.just(date),
            st.just(time + fraction),
            st.just(date + "T" + time + fraction),
            st.just(date + " " + time + fraction + zone),
            st.just(date + "T" + time + fraction + zone),
        )
    )


scalar_value = st.one_of(
    string_value,
    integer_value,
    floating_value(),
    st.sampled_from(["true", "false"]),
    date_time_value(),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
)


def _containers(children):
    arrays = st.lists(children, min_size=0, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + "]"
    )
    arrays_with_newlines = st.lists(children, min_size=0, max_size=3).map(
        lambda xs: "[\n" + "\n".join(xs) + "\n]"
    )
    inline_pairs = st.lists(
        st.tuples(key(), children), min_size=0, max_size=4
    ).map(
        lambda pairs: "{"
        + ", ".join(pair[0] + " = " + pair[1] for pair in pairs)
        + "}"
    )
    duplicate_inline = st.tuples(key(), children, children).map(
        lambda p: "{"
        + p[0]
        + " = "
        + p[1]
        + ", "
        + p[0]
        + " = "
        + p[2]
        + "}"
    )
    trailing_inline = st.lists(
        st.tuples(key(), children), min_size=1, max_size=4
    ).map(
        lambda pairs: "{"
        + ", ".join(pair[0] + " = " + pair[1] for pair in pairs)
        + ", }"
    )
    newline_inline = st.tuples(key(), children).map(
        lambda p: "{\n" + p[0] + " = " + p[1] + "}"
    )
    return st.one_of(
        arrays,
        arrays,
        arrays_with_newlines,
        inline_pairs,
        inline_pairs,
        duplicate_inline,
        trailing_inline,
        newline_inline,
    )


value = st.recursive(
    scalar_value,
    _containers,
    max_leaves=80,
)


@composite
def pair(draw):
    return draw(key()) + " = " + draw(value)


@composite
def duplicate_pairs(draw):
    k = draw(key())
    return k + " = " + draw(value) + "\n" + k + " = " + draw(value)


@composite
def table_line(draw):
    return draw(
        st.one_of(
            key().map(lambda k: "[" + k + "]"),
            key().map(lambda k: "[[" + k + "]]"),
        )
    )


@composite
def document(draw):
    lines = draw(
        st.lists(
            st.one_of(pair(), pair(), duplicate_pairs(), table_line()),
            min_size=0,
            max_size=10,
        )
    )
    return "\n".join(lines)


@composite
def malformed_document(draw):
    return draw(
        st.one_of(
            st.just("k 1"),
            st.just("k = [1"),
            st.just("k = {a = 1"),
            st.just('k = "unterminated'),
            st.just("[unterminated"),
            st.just("k = {a = 1\nb = 2}"),
        )
    )


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=48000, max_value=100000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=80000, max_value=115000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=90000, max_value=130000))
    return "a." * n + "k"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60000, max_value=80000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20000, max_value=45000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc(draw, shape):
    return "deep = " + draw(shape)


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[a]"] + ["k" + str(i) + " = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 20),
    malformed_document(),
    deep_doc(deep_array()),
    deep_doc(deep_inline_table()),
    deep_doc(deep_dotted_key()),
    deep_doc(deep_mixed_nesting()),
    deep_doc(deep_quoted_mixed()),
    many_siblings(),
)