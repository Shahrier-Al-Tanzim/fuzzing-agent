"""Generated strategy - iteration 0, attempt 3.
accepted: False
generated: 2026-09-02T23:20:09.524418+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_RAW = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?()[]{}"
LITERAL_RAW = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?()[]{}\""


@composite
def basic_string(draw):
    raw = draw(st.text(alphabet=BASIC_RAW, min_size=0, max_size=18))
    escaped = draw(
        st.lists(
            st.sampled_from(["\\n", "\\t", "\\r", "\\\"", "\\\\", "\\u0000", "\\u03A9"]),
            min_size=0,
            max_size=3,
        )
    )
    parts = list(raw) + escaped
    return '"' + "".join(parts) + '"'


@composite
def literal_string(draw):
    raw = draw(st.text(alphabet=LITERAL_RAW, min_size=0, max_size=18))
    return "'" + raw + "'"


@composite
def multiline_string(draw):
    raw = draw(st.text(alphabet=BASIC_RAW + "\n", min_size=0, max_size=28))
    return '"""' + raw.replace('"""', '"') + '"""'


@composite
def multiline_literal_string(draw):
    raw = draw(st.text(alphabet=LITERAL_RAW + "\n", min_size=0, max_size=28))
    return "'''" + raw.replace("'''", "''") + "'''"


@composite
def key(draw):
    unquoted = st.text(alphabet=UNQUOTED, min_size=1, max_size=10)
    quoted_basic = st.text(
        alphabet=BASIC_RAW.replace('"', ""),
        min_size=1,
        max_size=10,
    ).map(lambda x: '"' + x + '"')
    quoted_literal = st.text(
        alphabet=LITERAL_RAW.replace("'", ""),
        min_size=1,
        max_size=10,
    ).map(lambda x: "'" + x + "'")
    return draw(st.one_of(unquoted, quoted_basic, quoted_literal))


@composite
def dotted_key(draw):
    count = draw(st.integers(min_value=2, max_value=4))
    parts = draw(st.lists(key(), min_size=count, max_size=count))
    return ".".join(parts)


valid_key = st.one_of(key(), dotted_key())


@composite
def date_time(draw):
    year = draw(st.integers(min_value=1970, max_value=2100))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    fraction = draw(st.one_of(
        st.just(""),
        st.integers(min_value=0, max_value=9999999999999999999).map(
            lambda x: "." + str(x).zfill(19)
        ),
    ))
    zone = draw(st.one_of(
        st.just("Z"),
        st.tuples(
            st.sampled_from(["+", "-"]),
            st.integers(min_value=0, max_value=23),
            st.integers(min_value=0, max_value=59),
        ).map(lambda x: x[0] + f"{x[1]:02d}:{x[2]:02d}"),
    ))
    kind = draw(st.integers(min_value=0, max_value=3))
    date = f"{year:04d}-{month:02d}-{day:02d}"
    time = f"{hour:02d}:{minute:02d}:{second:02d}{fraction}"
    if kind == 0:
        return date + "T" + time + zone
    if kind == 1:
        return date + "T" + time
    if kind == 2:
        return date
    return time


valid_integer = st.one_of(
    *([st.sampled_from(["0", "-0", "1", "-1", "42", "-42"])] * 5),
    st.integers(min_value=0, max_value=999999).map(str),
    st.integers(min_value=1, max_value=999999).map(lambda x: str(x) + "_" + str(x % 10)),
    st.just("9223372036854775807"),
    st.just("-9223372036854775808"),
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("007"),
    st.just("-007"),
    st.integers(min_value=0, max_value=65535).map(lambda x: "0x" + f"{x:x}"),
    st.integers(min_value=0, max_value=65535).map(lambda x: "0o" + format(x, "o")),
    st.integers(min_value=0, max_value=255).map(lambda x: "0b" + format(x, "b")),
)

valid_float = st.one_of(
    st.just("0.0"),
    st.just("-0.0"),
    st.just("1.5"),
    st.just("-1.5"),
    st.just("1e10"),
    st.just("-2.5E-4"),
    st.just("1_000.5"),
    st.just("1e+2"),
    st.just("inf"),
    st.just("-inf"),
    st.just("nan"),
)

scalar = st.one_of(
    *([valid_integer] * 5),
    *([valid_float] * 3),
    st.just("true"),
    st.just("false"),
    basic_string(),
    literal_string(),
    multiline_string(),
    multiline_literal_string(),
    date_time(),
)

value = st.recursive(
    scalar,
    lambda child: st.one_of(
        st.lists(child, min_size=0, max_size=3).map(
            lambda xs: "[" + ", ".join(xs) + "]"
        ),
        st.lists(st.tuples(key(), child), min_size=0, max_size=3).map(
            lambda xs: "{}"
            if not xs
            else "{"
            + ", ".join(k + " = " + v for k, v in xs)
            + "}"
        ),
        st.lists(st.tuples(key(), child), min_size=1, max_size=3).map(
            lambda xs: "{"
            + ", ".join(k + " = " + v for k, v in xs)
            + ",}"
        ),
    ),
    max_leaves=35,
)


@composite
def valid_document(draw):
    count = draw(st.integers(min_value=1, max_value=5))
    lines = []
    for index in range(count):
        lines.append("k" + str(index) + " = " + draw(value))
    return "\n".join(lines)


@composite
def table_document(draw):
    count = draw(st.integers(min_value=1, max_value=3))
    lines = []
    for index in range(count):
        header = draw(key())
        lines.append("section" + str(index) + "." + header + " = " + draw(value))
    return "\n".join(lines)


@composite
def header_document(draw):
    name = draw(valid_key)
    kind = draw(st.sampled_from(["[", "[["]))
    close = "]" if kind == "[" else "]]"
    return kind + name + close


@composite
def duplicate_document(draw):
    return "dup = " + draw(scalar) + "\ndup = " + draw(scalar)


@composite
def malformed_document(draw):
    return draw(st.one_of(
        st.just("missing_equals 1"),
        st.just("x = [1, 2"),
        st.just('x = "unclosed'),
        st.just("x = {a = 1\n"),
        st.just("x = 1,"),
        st.just(r'x = "\q"'),
        st.just("x = {a = 1, a = 2}"),
    ))


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60000, max_value=70000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85000, max_value=90000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100000, max_value=105000))
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
def deep_value_document(draw, strategy):
    return "deep = " + draw(strategy)


@composite
def deep_key_document(draw):
    return draw(strategy) + " = 1"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=30000))
    lines = ["[siblings]"]
    lines.extend("k" + str(i) + " = 1" for i in range(n))
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([valid_document()] * 25),
    *([table_document()] * 3),
    *([header_document()] * 2),
    st.just(""),
    duplicate_document(),
    malformed_document(),
    deep_value_document(deep_array()),
    deep_value_document(deep_inline_table()),
    deep_key_document(deep_dotted_key()),
    deep_value_document(deep_mixed_nesting()),
    deep_value_document(deep_quoted_mixed()),
    many_siblings(),
)