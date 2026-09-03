"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-03T15:56:28.064195+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
QUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
)
PLAIN_STRING_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
)
LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&\"()*+,-./:;<=>?@[]^_`{|}~😀"
)


unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)
basic_key = st.one_of(
    unquoted_key,
    st.text(alphabet=QUOTED_KEY_CHARS, min_size=0, max_size=12).map(
        lambda s: '"' + s + '"'
    ),
    st.text(alphabet=LITERAL_CHARS, min_size=0, max_size=12).map(
        lambda s: "'" + s + "'"
    ),
)


@composite
def dotted_key(draw):
    parts = draw(
        st.lists(basic_key, min_size=1, max_size=5)
    )
    if len(parts) == 1:
        return parts[0]
    return ".".join(parts)


key = dotted_key


basic_string = st.one_of(
    st.text(alphabet=PLAIN_STRING_CHARS, min_size=0, max_size=24).map(
        lambda s: '"' + s + '"'
    ),
    st.sampled_from(
        [
            r'"\n"',
            r'"\t"',
            r'\"',
            r'"\\"',
            r'"\u0000"',
            r'"\u0041"',
            r'"\u20ac"',
            r'"\U0001f600"',
            r'"a\nb\tc\\"',
        ]
    ),
)

literal_string = st.text(
    alphabet=LITERAL_CHARS, min_size=0, max_size=24
).map(lambda s: "'" + s + "'")

multiline_basic = st.text(
    alphabet=PLAIN_STRING_CHARS + "\n", min_size=0, max_size=40
).map(lambda s: '"""' + s + '"""')

multiline_literal = st.text(
    alphabet=LITERAL_CHARS + "\n", min_size=0, max_size=40
).map(lambda s: "'''" + s + "'''")

invalid_string = st.sampled_from(
    [
        r'"\q"',
        r'"\x20"',
        r'"\u12"',
        r'"unterminated',
        "'unterminated",
        '"""unterminated',
        "'''unterminated",
    ]
)

string_value = st.one_of(
    basic_string,
    literal_string,
    multiline_basic,
    multiline_literal,
    invalid_string,
)


decimal_digits = st.one_of(
    st.sampled_from(["0", "1", "7", "42", "007", "0001", "9223372036854775807"]),
    st.integers(-10**18, 10**18).map(str),
    st.sampled_from(
        [
            "-0",
            "+0",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "1_000",
            "9_223_372_036_854_775_807",
            "18_446_744_073_709_551_615",
        ]
    ),
)

hex_integer = st.sampled_from(
    ["0x0", "0x1", "0x7f", "0xDEAD_BEEF", "0xFFFFFFFFFFFFFFFF"]
)
oct_integer = st.sampled_from(["0o0", "0o7", "0o755", "0o7_777"])
bin_integer = st.sampled_from(["0b0", "0b1", "0b1010", "0b1111_0000"])

integer_value = st.one_of(
    decimal_digits,
    hex_integer,
    oct_integer,
    bin_integer,
)

exponent = st.one_of(
    st.sampled_from(["e0", "E0", "e+10", "E-10", "e03"]),
    st.integers(-20, 20).map(lambda n: "e" + ("+" if n >= 0 else "") + str(n)),
)
fraction = st.one_of(
    st.sampled_from([".0", ".5", ".9999999999999999999", ".1_2"]),
    st.integers(0, 999999999).map(lambda n: "." + str(n)),
)

floating_value = st.one_of(
    st.sampled_from(["0.0", "-0.0", "+0.0", "1.0", "-12.50"]),
    st.tuples(decimal_digits, fraction).map(lambda p: p[0] + p[1]),
    st.tuples(decimal_digits, exponent).map(lambda p: p[0] + p[1]),
    st.tuples(decimal_digits, fraction, exponent).map(
        lambda p: p[0] + p[1] + p[2]
    ),
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


def extend_values(child):
    array_values = st.lists(child, min_size=0, max_size=5).map(
        lambda xs: "[" + ", ".join(xs) + "]"
    )
    array_with_trailing_comma = st.lists(child, min_size=1, max_size=4).map(
        lambda xs: "[" + ", ".join(xs) + ",]"
    )
    inline_pairs = st.lists(
        st.tuples(basic_key, child), min_size=0, max_size=4
    ).map(
        lambda xs: "{" + ", ".join(k + " = " + v for k, v in xs) + "}"
    )
    inline_duplicates = st.tuples(
        basic_key, child, child
    ).map(
        lambda x: "{" + x[0] + " = " + x[1] + ", " + x[0] + " = " + x[2] + "}"
    )
    inline_trailing = st.lists(
        st.tuples(basic_key, child), min_size=1, max_size=4
    ).map(
        lambda xs: "{" + ", ".join(k + " = " + v for k, v in xs) + ",}"
    )
    return st.one_of(
        array_values,
        array_values,
        array_with_trailing_comma,
        inline_pairs,
        inline_pairs,
        inline_duplicates,
        inline_trailing,
    )


value = st.recursive(
    scalar_value,
    extend_values,
    max_leaves=40,
)


@composite
def assignment(draw):
    k = draw(key())
    v = draw(value)
    suffix = draw(
        st.one_of(
            st.just(""),
            st.just(" # generated"),
            st.sampled_from([" # x", " # fuzz", " # 0"]),
        )
    )
    return k + " = " + v + suffix


@composite
def table_header(draw):
    k = draw(key())
    return draw(
        st.one_of(
            st.just("[" + k + "]"),
            st.just("[[" + k + "]]"),
        )
    )


@composite
def ordinary_document(draw):
    lines = draw(
        st.lists(
            st.one_of(assignment(), table_header()),
            min_size=1,
            max_size=12,
        )
    )
    return "\n".join(lines)


duplicate_top_level = st.tuples(
    basic_key, value, value
).map(
    lambda x: x[0] + " = " + x[1] + "\n" + x[0] + " = " + x[2]
)

duplicate_inline = st.tuples(
    basic_key, value, value
).map(
    lambda x: "x = {" + x[0] + " = " + x[1] + ", " + x[0] + " = " + x[2] + "}"
)

malformed_document = st.sampled_from(
    [
        "x 1",
        "x = [1",
        "x = {a = 1",
        'x = "abc',
        "x = 'abc",
        "x = {a = 1\n}",
        "x = {a = 1,}",
        "x = [1,]",
        "x = [1,\n]",
        "x = {a = 1, b = 2,}",
        "x = [[1]",
        "x = '''abc",
    ]
)


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=48000, max_value=52000))
    leaf = draw(st.sampled_from(["0", "-0", "9223372036854775808"]))
    return "deep = " + ("[" * depth) + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=24000, max_value=40000))
    leaf = draw(st.sampled_from(["0", "true", '"😀"']))
    key_text = draw(
        st.sampled_from(["a", '"a"', "'a'", '"quoted key"'])
    )
    opening = "".join("{" + key_text + " = " for _ in range(depth))
    return "deep = " + opening + leaf + ("}" * depth)


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=30000, max_value=60000))
    part = draw(st.sampled_from(["a", "quoted", '"quoted key"', "'literal'"]))
    return "deep." + ".".join(part for _ in range(depth)) + " = 0"


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=12000, max_value=30000))
    prefix = draw(st.sampled_from(["k", "key", "quoted"]))
    lines = [
        prefix + str(i) + " = " + ("0" if i % 3 else "true")
        for i in range(count)
    ]
    return "\n".join(lines)


empty_document = st.just("")


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    duplicate_top_level,
    duplicate_inline,
    malformed_document,
    empty_document,
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
)