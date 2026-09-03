"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-02T22:51:06.106085+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
QUOTED_KEY_CHARS = (
    " !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)
LITERAL_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?-_"
)
LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?-_"
)
ML_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?-_\t\n"
)


@composite
def key(draw):
    unquoted = st.text(
        alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
    )
    quoted = st.text(
        alphabet=QUOTED_KEY_CHARS, min_size=1, max_size=12
    ).map(lambda text: '"' + text + '"')
    literal = st.text(
        alphabet=LITERAL_KEY_CHARS, min_size=1, max_size=12
    ).map(lambda text: "'" + text + "'")
    return draw(st.one_of(unquoted, quoted, literal))


@composite
def dotted_key(draw):
    return ".".join(draw(st.lists(key(), min_size=2, max_size=5)))


key_strategy = st.one_of(key(), dotted_key())


basic_string = st.one_of(
    st.just('""'),
    st.lists(
        st.sampled_from(
            [
                "a",
                "Z",
                "0",
                " ",
                "!",
                "\\n",
                "\\t",
                '\\"',
                "\\\\",
                "\\u0000",
                "\\u0041",
                "\\u20ac",
                "\\uabcd",
                "\\U0001F600",
            ]
        ),
        min_size=0,
        max_size=12,
    ).map(lambda parts: '"' + "".join(parts) + '"'),
    st.just('"unicode-😀-𝄞"'),
)


literal_string = st.one_of(
    st.just("''"),
    st.text(
        alphabet=LITERAL_CHARS, min_size=1, max_size=16
    ).map(lambda text: "'" + text + "'"),
)


ml_basic_string = st.one_of(
    st.just('""""""'),
    st.text(
        alphabet=ML_CHARS, min_size=0, max_size=30
    ).map(lambda text: '"""' + text + '"""'),
    st.just('"""line one\nline two\\\nline three"""'),
)


ml_literal_string = st.one_of(
    st.just("''''''"),
    st.text(
        alphabet=ML_CHARS, min_size=0, max_size=30
    ).map(lambda text: "'''" + text + "'''"),
    st.just("'''literal\nmultiline\ntext'''"),
)


string_value = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
)


decimal_integer = st.one_of(
    st.sampled_from(
        [
            "0",
            "-0",
            "1",
            "-1",
            "007",
            "-007",
            "0_0",
            "00_00",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "1_000",
            "9_223_372_036_854_775_807",
        ]
    ),
    st.integers(min_value=-1000000, max_value=1000000).map(str),
)


hex_integer = st.one_of(
    st.sampled_from(
        [
            "0x0",
            "0x1",
            "0x7f",
            "0xDEAD_BEEF",
            "0xffff_ffff_ffff_ffff",
        ]
    ),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(
        lambda value: "0x{:x}".format(value)
    ),
)


oct_integer = st.one_of(
    st.sampled_from(
        ["0o0", "0o7", "0o755", "0o12_345", "0o777_777"]
    ),
    st.integers(min_value=0, max_value=0o777777).map(
        lambda value: "0o{:o}".format(value)
    ),
)


bin_integer = st.one_of(
    st.sampled_from(
        ["0b0", "0b1", "0b1010", "0b1010_0101", "0b1111_0000"]
    ),
    st.integers(min_value=0, max_value=65535).map(
        lambda value: "0b{:b}".format(value)
    ),
)


integer_value = st.one_of(
    decimal_integer,
    hex_integer,
    oct_integer,
    bin_integer,
)


float_value = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "1.0",
            "-1.25",
            "3.141592653589793",
            "1e0",
            "-1E+10",
            "9.99e-10",
            "1_000.5",
            "1.0e+2",
            "inf",
            "-inf",
            "+inf",
            "nan",
            "-nan",
            "+nan",
        ]
    ),
    st.tuples(
        st.integers(min_value=0, max_value=9999),
        st.integers(min_value=0, max_value=999999),
        st.integers(min_value=-20, max_value=20),
    ).map(
        lambda parts: "{}.{}e{}".format(
            parts[0], parts[1], parts[2]
        )
    ),
)


date_time_value = st.one_of(
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(
        lambda parts: (
            "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
                parts[5],
            )
        )
    ),
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=9999999999999999999),
    ).map(
        lambda parts: (
            "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{}-07:00".format(
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
                parts[5],
                str(parts[6]).zfill(19),
            )
        )
    ),
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
    ).map(
        lambda parts: "{:04d}-{:02d}-{:02d}".format(
            parts[0], parts[1], parts[2]
        )
    ),
    st.tuples(
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(
        lambda parts: "{:02d}:{:02d}:{:02d}".format(
            parts[0], parts[1], parts[2]
        )
    ),
)


scalar_value = st.one_of(
    string_value,
    integer_value,
    float_value,
    st.sampled_from(["true", "false"]),
    date_time_value,
)


@composite
def recursive_value(draw):
    def extend(values):
        arrays = st.lists(
            values, min_size=0, max_size=3
        ).map(lambda items: "[" + ", ".join(items) + "]")
        inline_tables = st.lists(
            st.tuples(key_strategy, values),
            min_size=0,
            max_size=3,
        ).map(
            lambda items: "{"
            + ", ".join(
                pair[0] + " = " + pair[1] for pair in items
            )
            + "}"
        )
        return st.one_of(
            arrays,
            arrays,
            inline_tables,
            inline_tables,
        )

    return draw(st.recursive(scalar_value, extend, max_leaves=20))


@composite
def biased_recursive_value(draw):
    def extend(values):
        arrays = st.lists(
            values, min_size=1, max_size=2
        ).map(lambda items: "[" + ", ".join(items) + "]")
        inline_tables = st.lists(
            st.tuples(key_strategy, values),
            min_size=1,
            max_size=2,
        ).map(
            lambda items: "{"
            + ", ".join(
                pair[0] + " = " + pair[1] for pair in items
            )
            + "}"
        )
        return st.one_of(
            arrays,
            arrays,
            arrays,
            arrays,
            inline_tables,
            inline_tables,
            inline_tables,
            values,
        )

    return draw(st.recursive(scalar_value, extend, max_leaves=28))


@composite
def pair(draw):
    return draw(key_strategy) + " = " + draw(recursive_value())


@composite
def biased_pair(draw):
    return draw(key_strategy) + " = " + draw(biased_recursive_value())


@composite
def table_header(draw):
    return "[" + draw(key_strategy) + "]"


@composite
def array_table_header(draw):
    return "[[" + draw(key_strategy) + "]]"


@composite
def ordinary_document(draw):
    one_line = st.one_of(
        pair(),
        table_header(),
        array_table_header(),
    )
    structured = st.tuples(
        table_header(),
        pair(),
        pair(),
    ).map(lambda parts: "\n".join(parts))
    two_lines = st.tuples(
        pair(),
        pair(),
    ).map(lambda parts: "\n".join(parts))
    return draw(
        st.one_of(
            one_line,
            one_line,
            one_line,
            two_lines,
            structured,
        )
    )


@composite
def biased_document(draw):
    header = draw(st.one_of(table_header(), array_table_header()))
    lines = draw(st.lists(biased_pair(), min_size=1, max_size=3))
    return "\n".join([header] + lines)


duplicate_key = st.one_of(
    st.sampled_from(["x", "a", "duplicate", "same"]),
    key(),
)


@composite
def duplicate_document(draw):
    k = draw(duplicate_key)
    value1 = draw(recursive_value())
    value2 = draw(recursive_value())
    return k + " = " + value1 + "\n" + k + " = " + value2


duplicate_document_examples = st.one_of(
    duplicate_document(),
    duplicate_document(),
    duplicate_document(),
    st.just('"duplicate key" = 1\n"duplicate key" = 2'),
    st.just("a.b = 1\na.b = 2"),
    st.just("x = {a = 1, a = 2}"),
    st.just("x = {a = 1, b = 2, a = 3}"),
    st.just('x = {"same" = 1, "same" = 2}'),
    st.just("x = 1\nx = 2\nx = 3"),
)


valid_special_document = st.one_of(
    st.just("x = inf"),
    st.just("x = -inf"),
    st.just("x = +inf"),
    st.just("x = nan"),
    st.just("x = -nan"),
    st.just("x = +nan"),
    st.just("x = 9223372036854775808"),
    st.just("x = -9223372036854775809"),
    st.just("x = {a = 1, b = 2, }"),
    st.just("x = []"),
    st.just("x = {}"),
)


malformed_document = st.one_of(
    st.just("x 1"),
    st.just("x = {a = 1"),
    st.just("x = [1, 2"),
    st.just('x = "unclosed'),
    st.just("x = 'unclosed"),
    st.just("x = {a = 1,\nb = 2}"),
    st.just("x = [1, 2,]"),
    st.just("[unclosed"),
    st.just("[[unclosed]]"),
    st.just('x = "bad\\q"'),
    st.just("x = {a = 1,\n"),
    st.just("x = 007"),
    st.just("x = -007"),
    st.just("x = 0_0"),
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


def deep_value_document(strategy):
    return strategy.map(lambda value: "deep = " + value)


deep_dotted_document = deep_dotted_key().map(
    lambda value: value + " = 1"
)


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[a]"]
    lines.extend("k" + str(index) + " = 1" for index in range(n))
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 24),
    biased_document(),
    duplicate_document_examples,
    valid_special_document,
    malformed_document,
    deep_value_document(deep_array()),
    deep_value_document(deep_inline_table()),
    deep_dotted_document,
    deep_value_document(deep_mixed_nesting()),
    deep_value_document(deep_quoted_mixed()),
    many_siblings(),
)