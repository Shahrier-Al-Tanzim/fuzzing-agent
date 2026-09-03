"""Generated strategy - iteration 2, attempt 2.
accepted: True
generated: 2026-09-03T16:09:28.194912+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
BASIC_KEY_CHARS = (
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
        alphabet=BASIC_KEY_CHARS, min_size=0, max_size=12
    ).map(lambda s: '"' + s + '"'),
    st.text(
        alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
    ).map(lambda s: "'" + s + "'"),
)


@composite
def dotted_key(draw):
    parts = draw(st.lists(basic_key, min_size=1, max_size=5))
    return ".".join(parts)


def key():
    return st.one_of(
        unquoted_key,
        st.text(
            alphabet=BASIC_KEY_CHARS, min_size=0, max_size=12
        ).map(lambda s: '"' + s + '"'),
        st.text(
            alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
        ).map(lambda s: "'" + s + "'"),
        dotted_key(),
    )


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
    alphabet=ML_BASIC_CHARS + "\n", min_size=0, max_size=40
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
            "007",
            "0001",
            "1_000",
            "9_223_372_036_854_775_807",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "18446744073709551615",
        ]
    ),
)

hex_integer = st.one_of(
    st.sampled_from(
        [
            "0x0",
            "0x1",
            "0x7f",
            "0xDEAD_BEEF",
            "0xFFFFFFFFFFFFFFFF",
            "0x1_0000",
        ]
    ),
    st.tuples(
        st.sampled_from(["0x", "0X"]),
        st.integers(0, 2**64 - 1).map(lambda n: format(n, "x")),
    ).map(lambda p: p[0] + p[1]),
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
            "1_000.000_1",
        ]
    ),
    st.tuples(
        st.integers(0, 999999),
        st.integers(0, 9999999999999999999),
    ).map(lambda p: f"{p[0]}.{p[1]:019d}"),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
)

boolean_value = st.sampled_from(["true", "false"])

date_time_value = st.one_of(
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
    ).map(lambda p: f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}T"
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}"
        )
    ),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(0, 9999999999999999999),
    ).map(lambda p: f"{p[0]:02d}:{p[1]:02d}:{p[2]:02d}.{p[3]:019d}"),
    st.tuples(
        st.integers(1970, 2099),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d} "
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}Z"
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
        lambda p: (
            f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}T"
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}{p[6]:+03d}:00"
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


def extend_values(child):
    arrays = st.lists(child, min_size=0, max_size=5).map(
        lambda xs: "[" + ", ".join(xs) + "]"
    )
    trailing_arrays = st.lists(child, min_size=1, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + ",]"
    )
    inline = st.lists(
        st.tuples(basic_key, child), min_size=0, max_size=4
    ).flatmap(
        lambda pairs: st.booleans().map(
            lambda trailing: (
                "{"
                + ", ".join(f"{p[0]} = {p[1]}" for p in pairs)
                + ("," if trailing and pairs else "")
                + "}"
            )
        )
    )
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

biased_value = st.recursive(
    scalar_value,
    lambda child: st.one_of(
        extend_values(child),
        extend_values(child),
        extend_values(child),
        extend_values(child),
        extend_values(child),
        st.lists(child, min_size=1, max_size=1).map(
            lambda xs: "[" + xs[0] + "]"
        ),
    ),
    max_leaves=80,
)

pair = st.tuples(
    key(),
    value,
    st.sampled_from(["", " # generated", " # fuzz", " # 0"]),
).map(lambda p: f"{p[0]} = {p[1]}{p[2]}")

biased_pair = st.tuples(
    key(),
    biased_value,
    st.sampled_from(["", " # deep", " # fuzz"]),
).map(lambda p: f"{p[0]} = {p[1]}{p[2]}")

table_header = st.one_of(
    key().map(lambda k: "[" + k + "]"),
    key().map(lambda k: "[[" + k + "]]"),
)


@composite
def ordinary_document(draw):
    count = draw(st.integers(min_value=1, max_value=12))
    lines = draw(
        st.lists(
            st.one_of(pair, table_header),
            min_size=count,
            max_size=count,
        )
    )
    return "\n".join(lines)


@composite
def biased_document(draw):
    count = draw(st.integers(min_value=1, max_value=5))
    lines = draw(
        st.lists(
            st.one_of(biased_pair, table_header),
            min_size=count,
            max_size=count,
        )
    )
    return "\n".join(lines)


@composite
def duplicate_document(draw):
    k = draw(key())
    first = draw(value)
    second = draw(value)
    return f"{k} = {first}\n{k} = {second}"


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=49000, max_value=62000))
    leaf = draw(st.one_of(boolean_value, integer_value, basic_string))
    return "deep = " + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_array_quoted_document(draw):
    depth = draw(st.integers(min_value=49000, max_value=62000))
    leaf = draw(st.one_of(literal_string, multiline_basic, boolean_value))
    return '"deep key" = ' + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=28000, max_value=46000))
    leaf = draw(st.one_of(basic_string, literal_string, boolean_value))
    quoted = draw(st.booleans())
    key_text = '"a key"' if quoted else "a"
    opening = "".join("{" + key_text + " = " for _ in range(depth))
    return "deep = " + opening + leaf + ("}" * depth)


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=32000, max_value=70000))
    quoted = draw(st.booleans())
    if quoted:
        parts = ['"quoted key"' if i % 2 else "'literal'" for i in range(depth)]
    else:
        parts = ["a" if i % 2 else "quoted" for i in range(depth)]
    return "deep." + ".".join(parts) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=30000, max_value=50000))
    prefix = draw(st.sampled_from(["k", "key", "quoted"]))
    lines = [
        f"{prefix}{i} = {'true' if i % 3 == 0 else '0'}"
        for i in range(count)
    ]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    biased_document(),
    duplicate_document(),
    deep_array_document(),
    deep_array_quoted_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
)