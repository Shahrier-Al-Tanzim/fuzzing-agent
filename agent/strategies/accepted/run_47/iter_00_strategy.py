"""Generated strategy - iteration 0, attempt 6.
accepted: True
generated: 2026-09-02T23:22:16.325256+00:00
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
            st.sampled_from(["\\n", "\\t", "\\\"", "\\\\", "\\u0000", "\\u0041", "\\u20ac"]),
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
def key(draw):
    unquoted = draw(st.booleans())
    if unquoted:
        return draw(st.text(alphabet=UNQUOTED, min_size=1, max_size=12))
    body = draw(st.text(
        alphabet=KEY_TEXT.replace('"', "").replace("\\", "").replace("\n", "").replace("\r", ""),
        min_size=1,
        max_size=12,
    ))
    return '"' + body + '"'


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
        st.integers(0, 9999999999999999999).map(lambda n: "." + str(n).zfill(19)),
        st.sampled_from([".1", ".12", ".999", ".999999"]),
    ))
    zone = draw(st.one_of(
        st.just(""),
        st.just("Z"),
        st.tuples(st.sampled_from(["+", "-"]), st.integers(0, 23), st.integers(0, 59))
        .map(lambda x: x[0] + f"{x[1]:02d}:{x[2]:02d}"),
    ))
    kind = draw(st.sampled_from(["date", "time", "local_datetime", "offset_datetime"]))
    date = f"{year:04d}-{month:02d}-{day:02d}"
    time = f"{hour:02d}:{minute:02d}:{second:02d}{fraction}"
    if kind == "date":
        return date
    if kind == "time":
        return time
    return date + "T" + time + zone


normal_integer = st.sampled_from([
    "0", "-0", "1", "-1", "42", "-42",
    "9223372036854775807", "-9223372036854775808",
    "9223372036854775808", "-9223372036854775809",
    "1_000", "9_223_372_036_854_775_807",
    "0x0", "0x7fff_ffff", "0o0", "0o755", "0b0", "0b1010_1010",
])

normal_float = st.sampled_from([
    "0.0", "-0.0", "1.5", "-2.75", "1e0", "-1E+9",
    "3.14159", "1_000.5", "9.223372036854776e18",
    "inf", "-inf", "nan", "+nan",
])

normal_scalar = st.one_of(
    basic_string(),
    literal_string(),
    normal_integer,
    normal_float,
    st.sampled_from(["true", "false"]),
    date_time(),
)


def expand_value(child):
    array_values = st.lists(child, min_size=0, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + ("," if xs and False else "") + "]"
    )
    inline_values = st.lists(child, min_size=0, max_size=4).map(
        lambda xs: "{" + ", ".join("a" + str(i) + " = " + x for i, x in enumerate(xs)) + "}"
    )
    return st.one_of(
        array_values,
        inline_values,
        array_values,
        inline_values,
        child,
    )


value_strategy = st.recursive(
    normal_scalar,
    expand_value,
    max_leaves=32,
)


@composite
def ordinary_document(draw):
    pair_count = draw(st.integers(min_value=1, max_value=7))
    values = draw(st.lists(value_strategy, min_size=pair_count, max_size=pair_count))
    lines = [f"k{i} = {values[i]}" for i in range(pair_count)]

    add_table = draw(st.booleans())
    if add_table:
        table_name = draw(key())
        lines.insert(0, "[" + table_name + "]")

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
    n = draw(st.integers(min_value=10000, max_value=12000))
    return "\n".join(["[a]"] + [f"k{i} = 1" for i in range(n)])


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
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