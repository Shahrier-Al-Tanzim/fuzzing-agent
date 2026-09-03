"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-09-02T23:06:55.475286+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_SAFE = BASIC_SAFE.replace("'", "")
ML_BASIC_SAFE = BASIC_SAFE.replace('"', "").replace("\\", "")
ML_LITERAL_SAFE = BASIC_SAFE.replace("'", "")


@composite
def basic_string(draw):
    body = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=18))
    escaped = draw(
        st.lists(
            st.sampled_from(["\\n", "\\t", '\\"', "\\\\", "\\u0000", "\\u03a9", "\\u4e2d"]),
            min_size=0,
            max_size=3,
        )
    )
    pieces = []
    for item in draw(st.lists(st.integers(0, 2), min_size=len(escaped), max_size=len(escaped))):
        pieces.append(escaped[item % len(escaped)] if escaped else "")
    return '"' + body + "".join(pieces) + '"'


@composite
def literal_string(draw):
    return "'" + draw(st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=18)) + "'"


@composite
def ml_basic_string(draw):
    body = draw(st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=24))
    return '"""' + body + "\n" + draw(st.sampled_from(["", "text", "unicode \U0001f600"])) + '"""'


@composite
def ml_literal_string(draw):
    body = draw(st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=24))
    return "'''" + body + "\n" + draw(st.sampled_from(["", "text", "unicode \U0001f600"])) + "'''"


@composite
def key(draw):
    return draw(
        st.one_of(
            st.text(alphabet=UNQUOTED, min_size=1, max_size=10),
            st.text(alphabet=BASIC_SAFE, min_size=1, max_size=10).map(lambda x: '"' + x + '"'),
            st.text(alphabet=LITERAL_SAFE, min_size=1, max_size=10).map(lambda x: "'" + x + "'"),
        )
    )


@composite
def dotted_key(draw):
    parts = draw(st.lists(key(), min_size=2, max_size=3))
    return ".".join(parts)


integer = st.sampled_from(
    [
        "0",
        "-0",
        "1",
        "-1",
        "42",
        "-42",
        "9223372036854775807",
        "-9223372036854775808",
        "9223372036854775808",
        "-9223372036854775809",
        "1_000_000",
        "-9_223_372_036_854_775_808",
        "0x0",
        "0x7fff_ffff",
        "0o755",
        "0b1010_0101",
    ]
)

floating = st.sampled_from(
    [
        "0.0",
        "-0.0",
        "1.5",
        "-2.75",
        "1e10",
        "-2.5E-3",
        "1_000.5",
        "9.223372036854776e18",
        "inf",
        "-inf",
        "nan",
        "-nan",
    ]
)

date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 999999999),
    ).map(
        lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}T{x[3]:02d}:{x[4]:02d}:{x[5]:02d}.{x[6]:09d}Z"
    ),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}"),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda x: f"{x[0]:02d}:{x[1]:02d}:{x[2]:02d}"),
)


scalar = st.one_of(
    basic_string(),
    literal_string(),
    ml_basic_string(),
    ml_literal_string(),
    integer,
    floating,
    st.sampled_from(["true", "false"]),
    date_time,
)


@composite
def inline_table_value(draw, children):
    pairs = draw(st.lists(st.tuples(key(), children), min_size=0, max_size=3))
    return "{" + ", ".join(k + " = " + v for k, v in pairs) + "}"


@composite
def array_value(draw, children):
    values = draw(st.lists(children, min_size=0, max_size=4))
    return "[" + ", ".join(values) + "]"


value = st.recursive(
    scalar,
    lambda children: st.one_of(
        array_value(children),
        array_value(children),
        inline_table_value(children),
        inline_table_value(children),
    ),
    max_leaves=18,
)


@composite
def ordinary_document(draw):
    count = draw(st.integers(1, 4))
    values = draw(st.lists(value, min_size=count, max_size=count))
    lines = [f"{'key' + str(i)} = {values[i]}" for i in range(count)]
    return "\n".join(lines)


@composite
def table_document(draw):
    count = draw(st.integers(1, 3))
    values = draw(st.lists(value, min_size=count, max_size=count))
    header = draw(st.one_of(key(), dotted_key()))
    lines = [f"[{header}]"]
    lines.extend(f"{'member' + str(i)} = {values[i]}" for i in range(count))
    return "\n".join(lines)


@composite
def array_table_document(draw):
    count = draw(st.integers(1, 3))
    values = draw(st.lists(value, min_size=count, max_size=count))
    header = draw(st.one_of(key(), dotted_key()))
    lines = [f"[[{header}]]"]
    lines.extend(f"{'member' + str(i)} = {values[i]}" for i in range(count))
    return "\n".join(lines)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=48000, max_value=52000))
    return "deep = " + ("[" * n) + "1" + ("]" * n)


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=80000, max_value=85000))
    return "deep = " + ("{a=" * n) + "1" + ("}" * n)


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100000, max_value=105000))
    return ("a." * n) + "k = 1"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60000, max_value=65000))
    return "deep = " + ("[{a=" * n) + "1" + ("}]" * n)


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20000, max_value=25000))
    return "deep = " + ('[{"k"=' * n) + "1" + ("}]" * n)


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=30000))
    return "[siblings]\n" + "\n".join(f"k{i} = 1" for i in range(n))


trailing_inline = st.sampled_from(
    [
        "x = {a = 1, b = 2,}",
        "x = {a = 1,}",
        "x = {a = [1, 2,],}",
    ]
)

duplicate_document = st.sampled_from(
    [
        "x = 1\nx = 2",
        "x = {a = 1, a = 2}",
        "[a]\nx = 1\nx = 2",
    ]
)

malformed_document = st.sampled_from(
    [
        'x = "\\q"',
        'x = "\\u12"',
        'x = "unterminated',
        "x = [1, 2",
        "x = {a = 1\n}",
        "x 1",
    ]
)

toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    table_document(),
    table_document(),
    array_table_document(),
    trailing_inline,
    duplicate_document,
    malformed_document,
    st.just(""),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed(),
    many_siblings(),
)