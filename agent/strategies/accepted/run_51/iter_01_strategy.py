"""Generated strategy - iteration 1, attempt 4.
accepted: True
generated: 2026-09-03T16:03:39.648275+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
QUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
)
LITERAL_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    '!#$%&"()*+,-./:;<=>?@[]^_`{|}~😀'
)
PLAIN_STRING_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
)
ML_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
)
ML_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    '!#$%&"()*+,-./:;<=>?@[]^_`{|}~😀'
)


unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)

basic_key = st.one_of(
    unquoted_key,
    st.text(
        alphabet=QUOTED_KEY_CHARS, min_size=0, max_size=12
    ).map(lambda s: '"' + s + '"'),
    st.text(
        alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
    ).map(lambda s: "'" + s + "'"),
)


@composite
def dotted_key(draw):
    parts = draw(st.lists(basic_key, min_size=1, max_size=5))
    return ".".join(parts)


key = dotted_key


basic_string = st.one_of(
    st.text(
        alphabet=PLAIN_STRING_CHARS, min_size=0, max_size=24
    ).map(lambda s: '"' + s + '"'),
    st.sampled_from(
        [
            r'"\n"',
            r'"\t"',
            r'"\""',
            r'"\\"',
            r'"\u0000"',
            r'"\u0041"',
            r'"\u20ac"',
            r'"\U0001f600"',
            r'"a\nb\tc\\""',
        ]
    ),
)

literal_string = st.text(
    alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=24
).map(lambda s: "'" + s + "'")

multiline_basic = st.text(
    alphabet=ML_BASIC_CHARS, min_size=0, max_size=40
).map(lambda s: '"""' + s + '"""')

multiline_literal = st.text(
    alphabet=ML_LITERAL_CHARS + "\n", min_size=0, max_size=40
).map(lambda s: "'''" + s + "'''")

string_value = st.one_of(
    basic_string,
    literal_string,
    multiline_basic,
    multiline_literal,
)


decimal_value = st.one_of(
    st.integers(-10**12, 10**12).map(str),
    st.sampled_from(
        [
            "0",
            "-0",
            "+0",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "1_000",
            "9_223_372_036_854_775_807",
            "007",
            "0001",
        ]
    ),
)

hex_integer = st.sampled_from(
    [
        "0x0",
        "0x1",
        "0x7f",
        "0xDEAD_BEEF",
        "0xFFFFFFFFFFFFFFFF",
        "0x1_0000",
    ]
)
oct_integer = st.sampled_from(
    ["0o0", "0o7", "0o755", "0o7_777", "0o1_234"]
)
bin_integer = st.sampled_from(
    ["0b0", "0b1", "0b1010", "0b1111_0000", "0b1_0101"]
)

integer_value = st.one_of(
    decimal_value,
    hex_integer,
    oct_integer,
    bin_integer,
)

floating_value = st.one_of(
    st.sampled_from(
        [
            "0.0",
            "-0.0",
            "+0.0",
            "1.0",
            "-12.50",
            "1.2e3",
            "-1.2E-3",
            "9223372036854775808.0",
            "0.9999999999999999999",
            "1.2_3",
        ]
    ),
    st.tuples(
        st.integers(0, 999999),
        st.integers(0, 9999999999999999999),
    ).map(lambda x: f"{x[0]}.{x[1]:019d}"),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
)

boolean_value = st.sampled_from(["true", "false"])

date_time_value = st.one_of(
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda x: f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}"),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda x: (
            f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}T"
            f"{x[3]:02d}:{x[4]:02d}:{x[5]:02d}"
        )
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
    ).map(
        lambda x: f"{x[0]:02d}:{x[1]:02d}:{x[2]:02d}.{x[3]:019d}"
    ),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda x: (
            f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d} "
            f"{x[3]:02d}:{x[4]:02d}:{x[5]:02d}Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(-12, 12),
    ).map(
        lambda x: (
            f"{x[0]:04d}-{x[1]:02d}-{x[2]:02d}T"
            f"{x[3]:02d}:{x[4]:02d}:{x[5]:02d}"
            f"{x[6]:+03d}:00"
        )
    ),
)

scalar_value = st.one_of(
    string_value,
    integer_value,
    floating_value,
    boolean_value,
    date_time_value,
)


@composite
def inline_table_value(draw, child):
    keys = draw(st.lists(basic_key, min_size=0, max_size=4, unique=True))
    values = [draw(child) for _ in keys]
    body = ", ".join(
        f"{k} = {v}" for k, v in zip(keys, values)
    )
    trailing = draw(st.booleans())
    if trailing and body:
        body += ","
    return "{" + body + "}"


def extend_values(child):
    arrays = st.lists(
        child, min_size=0, max_size=5
    ).map(lambda xs: "[" + ", ".join(xs) + "]")
    trailing_arrays = st.lists(
        child, min_size=1, max_size=4
    ).map(lambda xs: "[" + ", ".join(xs) + ",]")
    inline = inline_table_value(child)
    return st.one_of(
        arrays,
        arrays,
        trailing_arrays,
        inline,
        inline,
        inline,
    )


value = st.recursive(
    scalar_value,
    extend_values,
    max_leaves=40,
)


@composite
def assignment(draw, value_strategy=value):
    return (
        draw(key())
        + " = "
        + draw(value_strategy)
        + draw(st.sampled_from(["", " # generated", " # fuzz", " # 0"]))
    )


@composite
def ordinary_document(draw):
    count = draw(st.integers(min_value=1, max_value=12))
    keys = draw(st.lists(key(), min_size=count, max_size=count, unique=True))
    lines = []
    for k in keys:
        lines.append(
            k
            + " = "
            + draw(value)
            + draw(st.sampled_from(["", " # generated", " # fuzz"]))
        )
    return "\n".join(lines)


@composite
def table_document(draw):
    header = draw(key())
    count = draw(st.integers(min_value=1, max_value=8))
    keys = draw(st.lists(key(), min_size=count, max_size=count, unique=True))
    lines = [f"[{header}]"]
    for k in keys:
        lines.append(k + " = " + draw(value))
    return "\n".join(lines)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48000, max_value=56000))
    leaf = draw(st.sampled_from(["0", "true", '"x"']))
    return "deep = " + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=24000, max_value=42000))
    leaf = draw(st.one_of(basic_string, literal_string, boolean_value))
    key_text = draw(st.sampled_from(["a", '"a"', "'a'"]))
    opening = "".join(
        "{" + key_text + " = " for _ in range(depth)
    )
    return "deep = " + opening + leaf + ("}" * depth)


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=65000))
    part = draw(st.sampled_from(["a", "quoted", '"quoted key"', "'literal'"]))
    return "deep." + ".".join(part for _ in range(depth)) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=12000, max_value=26000))
    prefix = draw(st.sampled_from(["k", "key", "quoted"]))
    lines = [
        f"{prefix}{i} = {'true' if i % 3 == 0 else '0'}"
        for i in range(count)
    ]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 35),
    table_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
)