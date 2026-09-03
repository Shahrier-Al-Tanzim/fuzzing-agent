"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-09-02T23:14:12.554879+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_SAFE = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~"
)
BASIC_KEY_SAFE = BASIC_SAFE.replace('"', "").replace("\\", "")
LITERAL_SAFE = BASIC_SAFE.replace("'", "")
ML_BASIC_SAFE = BASIC_SAFE.replace('"', "").replace("\\", "")
ML_LITERAL_SAFE = BASIC_SAFE.replace("'", "")


@composite
def basic_string(draw):
    body = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=32))
    escaped = draw(
        st.lists(
            st.sampled_from(
                [
                    "\\n",
                    "\\t",
                    "\\r",
                    '\\"',
                    "\\\\",
                    "\\b",
                    "\\f",
                    "\\u0000",
                    "\\u0009",
                    "\\u03a9",
                    "\\u4e2d",
                    "\\U0001f600",
                ]
            ),
            min_size=0,
            max_size=8,
        )
    )
    return '"' + body + "".join(escaped) + '"'


@composite
def literal_string(draw):
    body = draw(st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=32))
    return "'" + body + "'"


@composite
def ml_basic_string(draw):
    body = draw(st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=64))
    suffix = draw(
        st.sampled_from(
            [
                "",
                "text",
                "unicode \U0001f600",
                "multiple\nlines\nof text",
            ]
        )
    )
    return '"""' + body + "\n" + suffix + '"""'


@composite
def ml_literal_string(draw):
    body = draw(st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=64))
    suffix = draw(
        st.sampled_from(
            [
                "",
                "text",
                "unicode \U0001f600",
                "multiple\nlines\nof text",
            ]
        )
    )
    return "'''" + body + "\n" + suffix + "'''"


@composite
def key(draw):
    return draw(
        st.one_of(
            st.text(alphabet=UNQUOTED, min_size=1, max_size=14),
            st.text(alphabet=BASIC_KEY_SAFE, min_size=1, max_size=14).map(
                lambda text: '"' + text + '"'
            ),
            st.text(alphabet=LITERAL_SAFE, min_size=1, max_size=14).map(
                lambda text: "'" + text + "'"
            ),
        )
    )


@composite
def dotted_key(draw):
    parts = draw(st.lists(key(), min_size=2, max_size=5))
    return ".".join(parts)


integer = st.one_of(
    st.sampled_from(
        [
            "0",
            "-0",
            "1",
            "-1",
            "42",
            "-42",
            "007",
            "-007",
            "0000000000000000000007",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "18446744073709551615",
            "-18446744073709551616",
            "1_000_000",
            "-9_223_372_036_854_775_808",
            "0x0",
            "0x7fff_ffff",
            "0xffff_ffff_ffff_ffff",
            "0o755",
            "0o777_777_777",
            "0b1010_0101",
            "0b1111_1111_1111_1111",
        ]
    ),
    st.integers(0, 10**18).map(str),
    st.integers(0, 10**18).map(lambda value: f"{value:_}"),
    st.integers(10**18, 10**20).map(str),
)


floating = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "1.5",
            "-2.75",
            "1e10",
            "-2.5E-3",
            "1_000.5",
            "9.223372036854776e18",
            "1.7976931348623157e308",
            "-1.7976931348623157e308",
            "inf",
            "-inf",
            "nan",
            "-nan",
        ]
    ),
    st.tuples(
        st.integers(0, 10**18).map(str),
        st.integers(0, 999999999).map(lambda value: f"{value:09d}"),
    ).map(lambda parts: parts[0] + "." + parts[1]),
    st.tuples(
        st.integers(1, 10**18).map(str),
        st.integers(-300, 300).map(str),
    ).map(lambda parts: parts[0] + "e" + parts[1]),
)


date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2100).map(lambda value: f"{value:04d}"),
        st.integers(1, 12).map(lambda value: f"{value:02d}"),
        st.integers(1, 28).map(lambda value: f"{value:02d}"),
        st.integers(0, 23).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(0, 9999999999999999999).map(str),
    ).map(
        lambda parts: (
            parts[0]
            + "-"
            + parts[1]
            + "-"
            + parts[2]
            + "T"
            + parts[3]
            + ":"
            + parts[4]
            + ":"
            + parts[5]
            + "."
            + parts[6]
            + "Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2100).map(lambda value: f"{value:04d}"),
        st.integers(1, 12).map(lambda value: f"{value:02d}"),
        st.integers(1, 28).map(lambda value: f"{value:02d}"),
    ).map(lambda parts: parts[0] + "-" + parts[1] + "-" + parts[2]),
    st.tuples(
        st.integers(0, 23).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
    ).map(lambda parts: parts[0] + ":" + parts[1] + ":" + parts[2]),
    st.tuples(
        st.integers(0, 23).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.sampled_from(["Z", "+00:00", "-07:00"]),
    ).map(
        lambda parts: (
            "1979-05-27T"
            + parts[0]
            + ":"
            + parts[1]
            + ":"
            + parts[2]
            + parts[3]
        )
    ),
    st.tuples(
        st.integers(1970, 2100).map(lambda value: f"{value:04d}"),
        st.integers(1, 12).map(lambda value: f"{value:02d}"),
        st.integers(1, 28).map(lambda value: f"{value:02d}"),
        st.integers(0, 23).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(0, 59).map(lambda value: f"{value:02d}"),
        st.integers(10**18, 10**19 - 1).map(str),
    ).map(
        lambda parts: (
            parts[0]
            + "-"
            + parts[1]
            + "-"
            + parts[2]
            + "T"
            + parts[3]
            + ":"
            + parts[4]
            + ":"
            + parts[5]
            + "."
            + parts[6]
            + "+00:00"
        )
    ),
)


scalar = st.one_of(
    basic_string(),
    literal_string(),
    ml_basic_string(),
    ml_literal_string(),
    st.text(alphabet=BASIC_SAFE, min_size=40, max_size=160).map(
        lambda text: '"' + text + '"'
    ),
    integer,
    floating,
    st.sampled_from(["true", "false"]),
    date_time,
)


@composite
def inline_table_value(draw, children):
    values = draw(st.lists(children, min_size=0, max_size=4))
    names = ["a", "b", "c", "d"][: len(values)]
    pairs = [
        names[index] + " = " + values[index]
        for index in range(len(values))
    ]
    text = "{" + ", ".join(pairs)
    if values and draw(st.booleans()):
        text += ","
    return text + "}"


@composite
def array_value(draw, children):
    values = draw(st.lists(children, min_size=0, max_size=5))
    separator = draw(st.sampled_from([", ", ",\n", ",\n  "]))
    text = "[" + separator.join(values)
    if values and draw(st.booleans()):
        text += ","
    return text + "]"


value = st.recursive(
    scalar,
    lambda children: st.one_of(
        array_value(children),
        array_value(children),
        array_value(children),
        inline_table_value(children),
        inline_table_value(children),
        inline_table_value(children),
    ),
    max_leaves=24,
)


biased_value = st.recursive(
    scalar,
    lambda children: st.one_of(
        array_value(children),
        array_value(children),
        array_value(children),
        array_value(children),
        array_value(children),
        inline_table_value(children),
        inline_table_value(children),
        inline_table_value(children),
        inline_table_value(children),
        inline_table_value(children),
    ),
    max_leaves=36,
)


@composite
def ordinary_document(draw):
    count = draw(st.integers(1, 5))
    values = draw(st.lists(value, min_size=count, max_size=count))
    return "\n".join(
        "key" + str(index) + " = " + values[index]
        for index in range(count)
    )


@composite
def biased_document(draw):
    count = draw(st.integers(1, 3))
    values = draw(st.lists(biased_value, min_size=count, max_size=count))
    return "\n".join(
        "payload" + str(index) + " = " + values[index]
        for index in range(count)
    )


@composite
def dotted_document(draw):
    return draw(dotted_key()) + " = " + draw(value)


@composite
def table_document(draw):
    count = draw(st.integers(1, 4))
    values = draw(st.lists(value, min_size=count, max_size=count))
    header = draw(st.one_of(key(), dotted_key()))
    lines = ["[" + header + "]"]
    lines.extend(
        "member" + str(index) + " = " + values[index]
        for index in range(count)
    )
    return "\n".join(lines)


@composite
def array_table_document(draw):
    count = draw(st.integers(1, 4))
    values = draw(st.lists(biased_value, min_size=count, max_size=count))
    header = draw(st.one_of(key(), dotted_key()))
    lines = ["[[" + header + "]]"]
    lines.extend(
        "member" + str(index) + " = " + values[index]
        for index in range(count)
    )
    return "\n".join(lines)


@composite
def nested_array_table_document(draw):
    header = draw(st.one_of(key(), dotted_key()))
    values = draw(st.lists(biased_value, min_size=2, max_size=4))
    lines = ["[[" + header + "]]"]
    lines.extend(
        "nested" + str(index) + " = " + values[index]
        for index in range(len(values))
    )
    return "\n".join(lines)


@composite
def duplicate_document(draw):
    value_text = draw(scalar)
    return "duplicate = " + value_text + "\nduplicate = " + value_text


@composite
def duplicate_scoped_document(draw):
    first = draw(scalar)
    second = draw(scalar)
    return "[first]\nduplicate = " + first + "\n[second]\nduplicate = " + second


@composite
def duplicate_inline_document(draw):
    first = draw(scalar)
    second = draw(scalar)
    return "x = {a = " + first + ", a = " + second + "}"


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=48000, max_value=60000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=80000, max_value=90000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100000, max_value=115000))
    return "a." * n + "k"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60000, max_value=70000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20000, max_value=35000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_array_document(draw):
    return "deep = " + draw(deep_array())


@composite
def deep_inline_table_document(draw):
    return "deep = " + draw(deep_inline_table())


@composite
def deep_dotted_key_document(draw):
    return draw(deep_dotted_key()) + " = 1"


@composite
def deep_mixed_nesting_document(draw):
    return "deep = " + draw(deep_mixed_nesting())


@composite
def deep_quoted_mixed_document(draw):
    return "deep = " + draw(deep_quoted_mixed())


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[siblings]"]
    lines.extend("k" + str(index) + " = 1" for index in range(n))
    return "\n".join(lines)


trailing_inline = st.sampled_from(
    [
        "x = {a = 1, b = 2,}",
        "x = {a = 1,}",
        "x = {a = [1, 2,],}",
        "x = {a = {b = 9223372036854775808,},}",
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
    biased_document(),
    dotted_document(),
    table_document(),
    table_document(),
    array_table_document(),
    nested_array_table_document(),
    trailing_inline,
    duplicate_document(),
    duplicate_document(),
    duplicate_scoped_document(),
    duplicate_inline_document(),
    malformed_document,
    st.just(""),
    deep_array_document(),
    deep_inline_table_document(),
    deep_dotted_key_document(),
    deep_mixed_nesting_document(),
    deep_quoted_mixed_document(),
    many_siblings(),
)