"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-09-03T13:15:48.077407+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/():"
LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()\""
ML_BASIC_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?/"
ML_LITERAL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n.,!?\""
COMMENT_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:;!?/()"


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
    content = draw(st.text(alphabet=LITERAL_SAFE, min_size=0, max_size=28))
    return "'" + content + "'"


@composite
def multiline_basic(draw):
    content = draw(st.text(alphabet=ML_BASIC_SAFE, min_size=0, max_size=48))
    return '"""' + content + '"""'


@composite
def multiline_literal(draw):
    content = draw(st.text(alphabet=ML_LITERAL_SAFE, min_size=0, max_size=48))
    return "'''" + content + "'''"



def unquoted_key():
    return st.text(alphabet=UNQUOTED, min_size=1, max_size=12)


def quoted_key():
    return st.text(
        alphabet=BASIC_SAFE,
        min_size=1,
        max_size=12,
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
    trailing = "{ " + ", ".join(pairs) + ", }" if pairs else "{ }"
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
def comment(draw):
    text = draw(st.text(alphabet=COMMENT_SAFE, min_size=0, max_size=24))
    return "#" + text


@composite
def clean_assignment_document(draw):
    count = draw(st.integers(min_value=1, max_value=8))
    values = draw(st.lists(value_strategy, min_size=count, max_size=count))
    lines = [
        "k" + str(index) + " = " + values[index]
        for index in range(count)
    ]
    if draw(st.booleans()):
        lines[0] = lines[0] + " " + draw(comment())
    return "\n".join(lines)


@composite
def comment_document(draw):
    value_a = draw(value_strategy)
    value_b = draw(value_strategy)
    first_comment = draw(comment())
    second_comment = draw(comment())
    return "\n".join(
        [
            "commented_a = " + value_a + " " + first_comment,
            second_comment,
            "commented_b = " + value_b,
        ]
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
    if draw(st.booleans()):
        lines[-1] = lines[-1] + " " + draw(comment())
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
def duplicate_scoped_document(draw):
    value_a = draw(value_strategy)
    value_b = draw(value_strategy)
    return "\n".join(
        [
            "[duplicate_left]",
            "same = " + value_a,
            "[duplicate_right]",
            "same = " + value_b,
        ]
    )


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
    depth = draw(st.integers(min_value=48000, max_value=70000))
    leaf = draw(
        st.sampled_from(
            ["0", "9223372036854775808", '"\\u03bb"', "nan", "true"]
        )
    )
    openings = []
    for index in range(depth):
        if index % 997 == 0:
            openings.append("[\n# array level\n")
        elif index % 2:
            openings.append("[ ")
        else:
            openings.append("[\t")
    return "deep_array = " + "".join(openings) + leaf + ("]" * depth)


@composite
def deep_array_quoted_document(draw):
    depth = draw(st.integers(min_value=48500, max_value=68000))
    leaf = draw(st.sampled_from(['"\\u03bb"', '"quoted"', "0"]))
    openings = []
    for index in range(depth):
        openings.append("[\n" if index % 3 == 0 else "[ ")
    return "deep_quoted_array = " + "".join(openings) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=50000))
    leaf = draw(st.sampled_from(["0", '"\\u03bb"', "inf", "true"]))
    quoted = draw(st.booleans())
    value = leaf
    for index in range(depth):
        if quoted and index % 2:
            name = '"quoted key"'
        elif index % 3 == 0:
            name = "a"
        else:
            name = "b"
        value = "{ " + name + " = " + value + " }"
    return "deep_inline = " + value


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=50000, max_value=70000))
    quoted = draw(st.booleans())
    names = []
    for index in range(depth):
        if quoted and index % 2:
            names.append('"quoted key"')
        elif index % 3 == 0:
            names.append("a")
        else:
            names.append("b")
    return ".".join(names) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=30000, max_value=40000))
    value = draw(st.sampled_from(["0", "1", '"x"', "true"]))
    lines = [
        "sibling" + str(index) + " = " + value
        for index in range(count)
    ]
    lines[0] = lines[0] + " " + draw(comment())
    return "\n".join(lines)


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
    *([clean_assignment_document()] * 16),
    clean_assignment_document(),
    clean_assignment_document(),
    table_document(),
    array_table_document(),
    comment_document(),
    duplicate_scoped_document(),
    duplicate_inline(),
    duplicate_assignment(),
    edge_document(),
    malformed_document,
    deep_array_document(),
    deep_array_quoted_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
)