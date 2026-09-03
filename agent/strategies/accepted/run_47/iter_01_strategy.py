"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-02T23:25:11.111397+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
KEY_TEXT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _.-"
STRING_TEXT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?:;_+-*/()[]{}<>"
ML_TEXT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?:;_+-*/()[]{}<>\n"


@composite
def basic_string(draw):
    parts = draw(st.lists(
        st.one_of(
            st.text(alphabet=STRING_TEXT, min_size=0, max_size=8),
            st.sampled_from([
                "\\n", "\\t", "\\\"", "\\\\", "\\u0000",
                "\\u0041", "\\u20ac", "\\U0001f600",
            ]),
            st.sampled_from(["😀", "𐍈", "𝄞"]),
        ),
        min_size=0,
        max_size=8,
    ))
    return '"' + "".join(parts) + '"'


@composite
def literal_string(draw):
    body = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?:;_+-*/()[]{}<>",
        min_size=0,
        max_size=24,
    ))
    return "'" + body + "'"


@composite
def multiline_basic_string(draw):
    body = draw(st.text(alphabet=ML_TEXT, min_size=0, max_size=48))
    return '"""' + body + '"""'


@composite
def multiline_literal_string(draw):
    body = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?:;_+-*/()[]{}<>\n",
        min_size=0,
        max_size=48,
    ))
    return "'''" + body + "'''"


simple_unquoted_key = st.text(
    alphabet=UNQUOTED,
    min_size=1,
    max_size=12,
)

quoted_key_body = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _.-,;:!?/[]{}()<>+=",
    min_size=1,
    max_size=12,
)


@composite
def simple_key(draw):
    if draw(st.booleans()):
        return draw(simple_unquoted_key)
    return '"' + draw(quoted_key_body) + '"'


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key(), min_size=2, max_size=4))
    return ".".join(parts)


@composite
def key(draw):
    return draw(st.one_of(simple_key(), dotted_key()))


@composite
def date_time(draw):
    year = draw(st.integers(1970, 2099))
    month = draw(st.integers(1, 12))
    day = draw(st.integers(1, 28))
    hour = draw(st.integers(0, 23))
    minute = draw(st.integers(0, 59))
    second = draw(st.integers(0, 59))

    fraction = draw(st.one_of(
        st.just(""),
        st.integers(0, 9999999999999999999).map(
            lambda n: "." + str(n).zfill(19)
        ),
        st.sampled_from([".1", ".12", ".999", ".999999"]),
    ))

    date = f"{year:04d}-{month:02d}-{day:02d}"
    time = f"{hour:02d}:{minute:02d}:{second:02d}{fraction}"

    kind = draw(st.sampled_from([
        "date", "time", "local_datetime", "offset_datetime"
    ]))

    if kind == "date":
        return date
    if kind == "time":
        return time

    if kind == "local_datetime":
        return date + "T" + time

    zone = draw(st.one_of(
        st.just("Z"),
        st.tuples(
            st.sampled_from(["+", "-"]),
            st.integers(0, 23),
            st.integers(0, 59),
        ).map(lambda x: x[0] + f"{x[1]:02d}:{x[2]:02d}"),
    ))
    return date + "T" + time + zone


normal_integer = st.sampled_from([
    "0", "-0", "1", "-1", "42", "-42",
    "9223372036854775807",
    "-9223372036854775808",
    "9223372036854775808",
    "-9223372036854775809",
    "007", "-009",
    "1_000",
    "9_223_372_036_854_775_807",
    "0x0", "0x7fff_ffff",
    "0o0", "0o755",
    "0b0", "0b1010_1010",
])


normal_float = st.sampled_from([
    "0.0", "-0.0", "1.5", "-2.75",
    "1e0", "-1E+9",
    "3.14159", "1_000.5",
    "9.223372036854776e18",
    "inf", "-inf", "+inf",
    "nan", "+nan", "-nan",
])


normal_scalar = st.one_of(
    basic_string(),
    literal_string(),
    multiline_basic_string(),
    multiline_literal_string(),
    normal_integer,
    normal_float,
    st.sampled_from(["true", "false"]),
    date_time(),
)


def expand_value(child):
    arrays = st.lists(child, min_size=0, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + "]"
    )

    inline_tables = st.lists(
        st.tuples(key(), child),
        min_size=0,
        max_size=4,
    ).map(
        lambda pairs: "{"
        + ", ".join(pair[0] + " = " + pair[1] for pair in pairs)
        + "}"
    )

    trailing_inline_tables = st.lists(
        st.tuples(key(), child),
        min_size=1,
        max_size=4,
    ).map(
        lambda pairs: "{"
        + ", ".join(pair[0] + " = " + pair[1] for pair in pairs)
        + ",}"
    )

    return st.one_of(
        arrays,
        inline_tables,
        inline_tables,
        trailing_inline_tables,
        child,
    )


value_strategy = st.recursive(
    normal_scalar,
    expand_value,
    max_leaves=32,
)


@composite
def pair(draw):
    return draw(key()) + " = " + draw(value_strategy)


comment_body = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?:;_+-*/()[]{}<>",
    min_size=0,
    max_size=32,
).map(lambda text: "#" + text)


@composite
def commented_pair(draw):
    result = draw(pair())
    if draw(st.booleans()):
        result += " " + draw(comment_body)
    return result


@composite
def standard_table_line(draw):
    return "[" + draw(key()) + "]"


@composite
def array_table_line(draw):
    return "[[" + draw(key()) + "]]"


@composite
def ordinary_document(draw):
    pair_count = draw(st.integers(min_value=1, max_value=7))
    lines = [draw(commented_pair()) for _ in range(pair_count)]

    if draw(st.booleans()):
        header = draw(st.one_of(
            standard_table_line(),
            array_table_line(),
        ))
        insert_at = draw(st.integers(min_value=0, max_value=len(lines)))
        lines.insert(insert_at, header)

    return "\n".join(lines)


@composite
def quoted_key_document(draw):
    quoted = '"' + draw(quoted_key_body) + '"'
    return quoted + " = " + draw(value_strategy)


@composite
def dotted_key_document(draw):
    return draw(dotted_key()) + " = " + draw(value_strategy)


@composite
def array_table_document(draw):
    header = "[[" + draw(key()) + "]]"
    entries = draw(st.lists(commented_pair(), min_size=1, max_size=4))
    return "\n".join([header] + entries)


@composite
def duplicate_key_document(draw):
    duplicate = draw(simple_key())
    first = duplicate + " = " + draw(normal_scalar)
    second = duplicate + " = " + draw(normal_scalar)
    return first + "\n" + second


@composite
def comment_document(draw):
    lines = draw(st.lists(commented_pair(), min_size=1, max_size=5))
    return "\n".join(lines)


@composite
def edge_document(draw):
    kind = draw(st.sampled_from([
        "empty_containers",
        "duplicates",
        "strings",
        "numbers",
        "malformed",
    ]))

    if kind == "empty_containers":
        return draw(st.sampled_from([
            "empty_array = []",
            "empty_table = {}",
            "empty_array = []\nempty_table = {}",
        ]))

    if kind == "duplicates":
        return draw(st.sampled_from([
            "x = 1\nx = 2",
            "x = {a = 1, a = 2}",
            "x = {a = 1, b = 2,}",
        ]))

    if kind == "strings":
        return draw(st.sampled_from([
            'basic = "\\n\\t\\\"\\\\\\u0041"',
            "literal = 'literal text'",
            'multi = """line one\nline two\nline three"""',
            "multi = '''line one\nline two\nline three'''",
            'unicode = "😀𐍈𝄞"',
        ]))

    if kind == "numbers":
        return draw(st.sampled_from([
            "zero = 0",
            "negative_zero = -0",
            "max = 9223372036854775807",
            "min = -9223372036854775808",
            "past_max = 9223372036854775808",
            "past_min = -9223372036854775809",
            "leading = 007",
            "special = [inf, -inf, nan]",
            "exponents = [1e2, -2E+3, 1_000.5]",
            "fraction = 1979-05-27T00:32:00.9999999999999999999-07:00",
        ]))

    return draw(st.sampled_from([
        'bad = "unclosed',
        "bad = [1, 2",
        "bad = {a = 1",
        "bad {a = 1}",
        "bad = {a = 1\n, b = 2}",
        "bad = '\\q'",
    ]))


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
    return "a." * n + "k = 1"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60000, max_value=65000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20000, max_value=25000))
    return '[{"k"=' * n + "1" + "}]" * n


def deep_value_document(shape):
    return shape().map(lambda value: "deep = " + value)


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    quoted_key_document(),
    dotted_key_document(),
    array_table_document(),
    duplicate_key_document(),
    comment_document(),
    edge_document(),
    edge_document(),
    edge_document(),
    deep_value_document(deep_array),
    deep_value_document(deep_inline_table),
    deep_dotted_key(),
    deep_value_document(deep_mixed_nesting),
    deep_value_document(deep_quoted_mixed),
    many_siblings(),
    st.just(""),
)