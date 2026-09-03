"""Generated strategy - iteration 2, attempt 3.
accepted: True
generated: 2026-09-03T13:13:22.978412+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()\""
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?\""


@composite
def basic_string(draw):
    ordinary = draw(st.text(alphabet=BASIC_SAFE, min_size=0, max_size=24))
    escaped = draw(
        st.lists(
            st.sampled_from(
                [
                    "\\n",
                    "\\t",
                    "\\r",
                    "\\b",
                    "\\f",
                    "\\\"",
                    "\\\\",
                    "\\/",
                    "\\u0000",
                    "\\u0041",
                    "\\u03bb",
                    "\\U0001f600",
                ]
            ),
            min_size=0,
            max_size=8,
        )
    )
    pieces = draw(st.permutations([ordinary] + escaped))
    return '"' + "".join(pieces) + '"'


@composite
def literal_string(draw):
    return "'" + draw(
        st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=28)
    ) + "'"


@composite
def multiline_basic(draw):
    content = draw(
        st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=48)
    )
    return '"""' + content + '"""'


@composite
def multiline_literal(draw):
    content = draw(
        st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=48)
    )
    return "'''" + content + "'''"


def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.text(
        alphabet=BASIC_SAFE, min_size=1, max_size=12
    ).map(lambda value: '"' + value + '"')


def simple_key():
    return st.one_of(unquoted_key(), quoted_key(), literal_string())


@composite
def key(draw):
    first = draw(simple_key())
    rest = draw(st.lists(simple_key(), min_size=0, max_size=3))
    return ".".join([first] + rest)


valid_decimal = st.one_of(
    st.just("0"),
    st.integers(min_value=1, max_value=999999).map(str),
    st.tuples(
        st.integers(min_value=1, max_value=999999),
        st.integers(min_value=1, max_value=999999),
    ).map(lambda pair: str(pair[0]) + "_" + str(pair[1])),
)

valid_integer = st.one_of(
    valid_decimal,
    st.tuples(
        st.integers(min_value=1, max_value=999999),
        st.integers(min_value=1, max_value=999999),
    ).map(lambda pair: "-" + str(pair[0]) + "_" + str(pair[1])),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(
        lambda number: "0x" + format(number, "x")
    ),
    st.integers(min_value=0, max_value=0o777777777).map(
        lambda number: "0o" + format(number, "o")
    ),
    st.integers(min_value=0, max_value=0b111111111).map(
        lambda number: "0b" + format(number, "b")
    ),
    st.sampled_from(
        [
            "-0",
            "12_34_567",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "9_223_372_036_854_775_807",
        ]
    ),
)

float_value = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "1.0",
            "-1.5",
            "3.1415926535",
            "1e0",
            "-1E+10",
            "6.02e23",
            "1_000.5",
            "9.9e-9",
            "inf",
            "+inf",
            "-inf",
            "nan",
            "+nan",
            "-nan",
        ]
    ),
    st.tuples(
        st.integers(min_value=-999999, max_value=999999).map(str),
        st.integers(min_value=0, max_value=999999).map(
            lambda number: f"{number:06d}"
        ),
        st.integers(min_value=-30, max_value=30),
    ).map(lambda parts: f"{parts[0]}.{parts[1]}e{parts[2]:+d}"),
    st.tuples(
        valid_decimal,
        st.integers(min_value=1, max_value=999999).map(
            lambda number: f"{number:06d}"
        ),
    ).map(lambda parts: f"{parts[0]}.{parts[1]}"),
)

date_value = st.one_of(
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda parts: f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda parts: (
            f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}T"
            f"{parts[3]:02d}:{parts[4]:02d}:{parts[5]:02d}"
        )
    ),
    st.tuples(
        st.integers(1970, 2100),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
        st.integers(-12, 12),
        st.integers(0, 59),
    ).map(
        lambda parts: (
            f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d} "
            f"{parts[3]:02d}:{parts[4]:02d}:{parts[5]:02d}."
            f"{parts[6]:019d}{parts[7]:+03d}:{parts[8]:02d}"
        )
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda parts: f"{parts[0]:02d}:{parts[1]:02d}:{parts[2]:02d}"),
)

scalar_value = st.one_of(
    st.just("0"),
    st.just("1"),
    st.just("true"),
    st.just("false"),
    basic_string(),
    literal_string(),
    multiline_basic(),
    multiline_literal(),
    valid_integer,
    float_value,
    date_value,
)


def array_strategy(child):
    return st.lists(
        st.one_of(child, child, child, child, child),
        min_size=0,
        max_size=4,
    ).map(lambda values: "[" + ", ".join(values) + "]")


@composite
def inline_strategy(draw, child):
    names = draw(
        st.permutations(["a", "b", "c", "d", "e", "f", "g", "h"])
    )
    count = draw(st.integers(min_value=0, max_value=4))
    values = draw(st.lists(child, min_size=count, max_size=count))
    pairs = [
        names[index] + " = " + values[index]
        for index in range(count)
    ]
    normal = "{ " + ", ".join(pairs) + " }"
    trailing = (
        "{ " + ", ".join(pairs) + ", }"
        if pairs
        else "{ }"
    )
    return draw(st.one_of(st.just(normal), st.just(trailing)))


value_strategy = st.recursive(
    scalar_value,
    lambda child: st.one_of(
        array_strategy(child),
        array_strategy(child),
        inline_strategy(child),
        inline_strategy(child),
    ),
    max_leaves=32,
)


@composite
def assignment(draw):
    return draw(key()) + " = " + draw(value_strategy)


@composite
def clean_assignment_document(draw):
    count = draw(st.integers(min_value=1, max_value=8))
    values = draw(st.lists(value_strategy, min_size=count, max_size=count))
    return "\n".join(
        "k" + str(index) + " = " + values[index]
        for index in range(count)
    )


@composite
def table_document(draw):
    count = draw(st.integers(min_value=1, max_value=6))
    values = draw(st.lists(value_strategy, min_size=count, max_size=count))
    header = draw(key())
    lines = [
        "table_root = 0",
        "[" + header + "]",
    ]
    lines.extend(
        "field" + str(index) + " = " + values[index]
        for index in range(count)
    )
    return "\n".join(lines)


@composite
def array_table_document(draw):
    count = draw(st.integers(min_value=1, max_value=6))
    values = draw(st.lists(value_strategy, min_size=count, max_size=count))
    header = draw(key())
    lines = [
        "array_root = 0",
        "[[" + header + "]]",
    ]
    lines.extend(
        "field" + str(index) + " = " + values[index]
        for index in range(count)
    )
    return "\n".join(lines)


@composite
def duplicate_inline(draw):
    value_a = draw(value_strategy)
    value_b = draw(value_strategy)
    return "x = { a = " + value_a + ", a = " + value_b + ", }"


@composite
def duplicate_assignment(draw):
    value_a = draw(value_strategy)
    value_b = draw(value_strategy)
    return "duplicate = " + value_a + "\nduplicate = " + value_b


@composite
def edge_document(draw):
    value = draw(
        st.sampled_from(
            [
                "007",
                "00042",
                "0_0",
                "9223372036854775808",
                "-9223372036854775809",
                "nan",
                "+nan",
                "-nan",
                '"\\u03bb"',
                '"\\U0001f600"',
            ]
        )
    )
    return "edge = " + value


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48750, max_value=62000))
    leaf = draw(st.sampled_from(["0", "9223372036854775808", '"\\u03bb"', "nan"]))
    return "deep = " + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=42000))
    leaf = draw(st.sampled_from(["0", '"\\u03bb"', "inf", "true"]))
    quoted = draw(st.booleans())
    value = leaf
    for index in range(depth):
        name = (
            '"quoted key"'
            if quoted and index % 2
            else ("a" if index % 2 == 0 else "b")
        )
        value = "{ " + name + " = " + value + " }"
    return "deep = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=52000))
    quoted = draw(st.booleans())
    names = [
        ('"a"' if index % 2 == 0 else '"quoted key"')
        if quoted
        else ("a" if index % 2 == 0 else "b")
        for index in range(depth)
    ]
    return ".".join(names) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=22000, max_value=32000))
    value = draw(st.sampled_from(["0", "1", '"x"', "true"]))
    return "\n".join(
        "sibling" + str(index) + " = " + value
        for index in range(count)
    )


malformed_document = st.one_of(
    st.just(""),
    st.just("x 1"),
    st.just("x = ["),
    st.just('x = "unterminated'),
    st.just("x = { a = 1\nb = 2 }"),
    st.just("x = [1, 2,]"),
    st.just("[broken"),
    st.just("[[broken]]\ny = 1"),
    st.just("x = '''unterminated\n"),
)

toml_strategy = st.one_of(
    *([clean_assignment_document()] * 12),
    clean_assignment_document(),
    clean_assignment_document(),
    table_document(),
    array_table_document(),
    edge_document(),
    duplicate_inline(),
    duplicate_assignment(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    malformed_document,
)