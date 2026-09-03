"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-09-02T23:20:36.487533+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_SAFE = BASIC_SAFE.replace("'", "")
ML_SAFE = BASIC_SAFE.replace('"', "").replace("\\", "")
ML_LITERAL_SAFE = BASIC_SAFE.replace("'", "")


@composite
def basic_string(draw):
    plain = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=18))
    escaped = draw(st.lists(
        st.sampled_from(["\\n", "\\t", '\\"', "\\\\", "\\u0000", "\\u0041",
                         "\\u03bb", "\\uD834\\uDD1E"]),
        min_size=0,
        max_size=4,
    ))
    parts = draw(st.permutations([plain] + escaped))
    return '"' + "".join(parts) + '"'


@composite
def literal_string(draw):
    return "'" + draw(st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=24)) + "'"


@composite
def multiline_basic(draw):
    body = draw(st.text(alphabet=ML_SAFE, min_size=0, max_size=32))
    return '"""' + body + '"""'


@composite
def multiline_literal(draw):
    body = draw(st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=32))
    return "'''" + body + "'''"


@composite
def key(draw):
    unquoted = draw(st.text(alphabet=UNQUOTED, min_size=1, max_size=12))
    quoted = draw(st.one_of(basic_string(), literal_string()))
    return draw(st.one_of(st.just(unquoted), st.just(quoted)))


@composite
def decimal_integer(draw):
    ordinary = draw(st.one_of(
        st.just("0"),
        st.just("-0"),
        st.integers(-1000000, 1000000).map(str),
        st.sampled_from([
            "1_000", "12_345_678", "-9_223_372_036_854_775_808",
            "9_223_372_036_854_775_807", "9223372036854775807",
            "-9223372036854775808", "9223372036854775808",
            "-9223372036854775809", "007", "-007", "00_7",
        ]),
    ))
    return ordinary


@composite
def other_integer(draw):
    h = draw(st.sampled_from(["0x0", "0xFF", "0xDEAD_BEEF", "0xFFFFFFFFFFFFFFFF"]))
    o = draw(st.sampled_from(["0o0", "0o755", "0o7_777"]))
    b = draw(st.sampled_from(["0b0", "0b1", "0b1010_0101", "0b11111111"]))
    return draw(st.one_of(st.just(h), st.just(o), st.just(b)))


@composite
def floating(draw):
    exponent = draw(st.sampled_from(["e0", "E+10", "e-10", "E_1", "e1_000"]))
    mantissa = draw(st.sampled_from([
        "0.0", "-0.0", "1.5", "10.000_001", "3.14159", "9223372036854775808.0"
    ]))
    return draw(st.one_of(
        st.just("inf"), st.just("-inf"), st.just("+inf"),
        st.just("nan"), st.just("-nan"), st.just("+nan"),
        st.just("1e0"), st.just("1E+10"), st.just("1e-10"),
        st.tuples(mantissa, exponent).map(lambda p: p[0] + p[1]),
        st.tuples(mantissa, st.just(".25")).map(lambda p: p[0].split(".")[0] + p[1]),
    ))


@composite
def date_time(draw):
    y = draw(st.integers(0, 9999))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    hh = draw(st.integers(0, 23))
    mm = draw(st.integers(0, 59))
    ss = draw(st.integers(0, 59))
    frac = draw(st.one_of(
        st.just(""),
        st.integers(0, 9999999999999999999).map(lambda n: "." + str(n).zfill(19)),
        st.sampled_from([".0", ".999", ".123456", ".9999999999999999999"]),
    ))
    local_date = f"{y:04d}-{m:02d}-{d:02d}"
    local_time = f"{hh:02d}:{mm:02d}:{ss:02d}{frac}"
    offset = draw(st.sampled_from(["", "Z", "+00:00", "-07:00", "+23:59"]))
    return draw(st.one_of(
        st.just(local_date),
        st.just(f"{hh:02d}:{mm:02d}:{ss:02d}{frac}"),
        st.just(local_date + "T" + local_time),
        st.just(local_date + " " + local_time + offset),
        st.just(local_date + "T" + local_time + offset),
    ))


scalar = st.one_of(
    basic_string(),
    literal_string(),
    multiline_basic(),
    multiline_literal(),
    decimal_integer(),
    other_integer(),
    floating(),
    st.sampled_from(["true", "false"]),
    date_time(),
    st.just(r'"\q"'),
    st.just(r'"\x00"'),
    st.just("'literal\nbroken'"),
)


def _array_value(children):
    return st.lists(children, min_size=0, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + "]"
    )


def _inline_value(children):
    pairs = st.lists(
        st.tuples(key(), children),
        min_size=0,
        max_size=4,
    ).map(lambda xs: ", ".join(k + " = " + v for k, v in xs))
    duplicate = st.tuples(key(), children, children).map(
        lambda x: x[0] + " = " + x[1] + ", " + x[0] + " = " + x[2]
    )
    trailing = st.lists(
        st.tuples(key(), children),
        min_size=1,
        max_size=4,
    ).map(lambda xs: ", ".join(k + " = " + v for k, v in xs) + ",")
    return st.one_of(
        pairs.map(lambda x: "{" + x + "}"),
        duplicate.map(lambda x: "{" + x + "}"),
        trailing.map(lambda x: "{" + x + "}"),
        st.just("{}"),
    )


nested_value = st.recursive(
    scalar,
    lambda children: st.one_of(
        _array_value(children),
        _inline_value(children),
        _array_value(children),
        _inline_value(children),
    ),
    max_leaves=35,
)


@composite
def dotted_key(draw):
    parts = draw(st.lists(key(), min_size=2, max_size=4))
    return ".".join(parts)


@composite
def pair(draw):
    k = draw(st.one_of(key(), dotted_key()))
    v = draw(nested_value)
    suffix = draw(st.one_of(st.just(""), st.just(" # comment")))
    return k + " = " + v + suffix


@composite
def standard_table(draw):
    return "[" + draw(key()) + "]"


@composite
def array_table(draw):
    return "[[" + draw(key()) + "]]"


@composite
def ordinary_document(draw):
    lines = draw(st.lists(
        st.one_of(pair(), standard_table(), array_table()),
        min_size=1,
        max_size=8,
    ))
    return "\n".join(lines)


@composite
def duplicate_document(draw):
    k = draw(key())
    v1 = draw(nested_value)
    v2 = draw(nested_value)
    return k + " = " + v1 + "\n" + k + " = " + v2


@composite
def malformed_document(draw):
    k = draw(key())
    v = draw(nested_value)
    malformed = draw(st.one_of(
        st.just(k + " " + v),
        st.just(k + " ="),
        st.just(k + " = [1, 2"),
        st.just(k + ' = "unclosed'),
        st.just(k + " = { a = 1\n, b = 2 }"),
        st.just(k + " = [1, 2,]"),
        st.just(k + " = {a = 1,}"),
    ))
    return malformed


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=48000, max_value=50000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=80000, max_value=85000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=90000, max_value=100000))
    return "a." * n + "k"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60000, max_value=65000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20000, max_value=25000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_value_document(draw, shape):
    return "deep = " + draw(shape)


@composite
def deep_key_document(draw, shape):
    return draw(shape) + " = 1"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    return "\n".join(["[a]"] + ["k" + str(i) + " = 1" for i in range(n)])


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    duplicate_document(),
    malformed_document(),
    st.just(""),
    deep_value_document(deep_array()),
    deep_value_document(deep_inline_table()),
    deep_key_document(deep_dotted_key()),
    deep_value_document(deep_mixed_nesting()),
    deep_value_document(deep_quoted_mixed()),
    many_siblings(),
)