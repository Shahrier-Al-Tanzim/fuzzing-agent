"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-03T16:25:28.709507+00:00
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
BASIC_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀"
    "\t"
)
LITERAL_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    '!#$%&"()*+,-./:;<=>?@[]^_`{|}~😀\t'
)
ML_BASIC_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~😀\t"
)
ML_LITERAL_BODY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    '!#$%&"()*+,-./:;<=>?@[]^_`{|}~😀\t'
)

unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)

quoted_basic_key = st.text(
    alphabet=BASIC_KEY_CHARS, min_size=0, max_size=12
).map(lambda s: f'"{s}"')

quoted_literal_key = st.text(
    alphabet=LITERAL_KEY_CHARS, min_size=0, max_size=12
).map(lambda s: f"'{s}'")

simple_key_strategy = st.one_of(
    unquoted_key, quoted_basic_key, quoted_literal_key
)


@composite
def dotted_key(draw, min_size=1, max_size=5):
    parts = draw(
        st.lists(
            simple_key_strategy,
            min_size=min_size,
            max_size=max_size,
        )
    )
    return ".".join(parts)


def key():
    return st.one_of(
        simple_key_strategy,
        dotted_key(),
    )


basic_string = st.one_of(
    st.text(
        alphabet=BASIC_BODY_CHARS,
        min_size=0,
        max_size=24,
    ).map(lambda s: f'"{s}"'),
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
    alphabet=LITERAL_BODY_CHARS,
    min_size=0,
    max_size=24,
).map(lambda s: f"'{s}'")

multiline_basic = st.text(
    alphabet=ML_BASIC_BODY_CHARS + "\n",
    min_size=0,
    max_size=40,
).map(lambda s: f'"""{s}"""')

multiline_literal = st.text(
    alphabet=ML_LITERAL_BODY_CHARS + "\n",
    min_size=0,
    max_size=40,
).map(lambda s: f"'''{s}'''")

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
    st.integers(0, 2**64 - 1).map(lambda n: f"0x{n:x}"),
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
            f"{p[3]:02d}:{p[4]:02d}:{p[5]:02d}"
            f"{p[6]:+03d}:00"
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
def inline_table_for(draw, child):
    keys = draw(
        st.lists(
            simple_key_strategy,
            min_size=0,
            max_size=5,
            unique=True,
        )
    )
    values = [draw(child) for _ in keys]
    trailing = draw(st.booleans())
    body = ", ".join(
        f"{k} = {v}" for k, v in zip(keys, values)
    )
    if trailing and keys:
        body += ","
    return "{" + body + "}"


def extend_values(child):
    arrays = st.lists(
        child,
        min_size=0,
        max_size=5,
    ).map(lambda xs: "[" + ", ".join(xs) + "]")
    trailing_arrays = st.lists(
        child,
        min_size=1,
        max_size=4,
    ).map(lambda xs: "[" + ", ".join(xs) + ",]")
    return st.one_of(
        arrays,
        trailing_arrays,
        inline_table_for(child),
        inline_table_for(child),
        inline_table_for(child),
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
    key().map(lambda k: f"[{k}]"),
    key().map(lambda k: f"[[{k}]]"),
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
def unique_pair_document(draw):
    count = draw(st.integers(min_value=1, max_value=18))
    keys = draw(
        st.lists(
            key(),
            min_size=count,
            max_size=count,
            unique=True,
        )
    )
    values = [draw(value) for _ in keys]
    comments = draw(
        st.lists(
            st.sampled_from(
                ["", " # generated", " # fuzz", " # comment"]
            ),
            min_size=count,
            max_size=count,
        )
    )
    return "\n".join(
        f"{k} = {v}{c}"
        for k, v, c in zip(keys, values, comments)
    )


@composite
def biased_document(draw):
    count = draw(st.integers(min_value=1, max_value=7))
    keys = draw(
        st.lists(
            key(),
            min_size=count,
            max_size=count,
            unique=True,
        )
    )
    values = [draw(biased_value) for _ in keys]
    return "\n".join(
        f"{k} = {v} # deep"
        for k, v in zip(keys, values)
    )


@composite
def duplicate_document(draw):
    k = draw(key())
    first = draw(value)
    second = draw(value)
    return f"{k} = {first}\n{k} = {second}"


@composite
def deep_array_document(draw):
    depth = draw(st.integers(min_value=90001, max_value=120000))
    leaf = draw(
        st.one_of(
            boolean_value,
            integer_value,
            basic_string,
            literal_string,
            st.sampled_from(
                [
                    "1979-05-27T00:32:00.9999999999999999999-07:00",
                    "0.9999999999999999999",
                ]
            ),
        )
    )
    spacing = draw(st.sampled_from(["", " ", "\t"]))
    openings = ("[" + spacing) * depth
    return "deep = " + openings + leaf + ("]" * depth)


@composite
def deep_inline_document(draw):
    depth = draw(st.integers(min_value=70001, max_value=110000))
    leaf = draw(
        st.one_of(
            basic_string,
            literal_string,
            boolean_value,
            integer_value,
        )
    )
    quoted = draw(st.booleans())
    parts = []
    for i in range(depth):
        if quoted:
            level_key = '"q"' if i % 2 else "'l'"
        else:
            level_key = "a" if i % 2 else "nested"
        parts.append("{")
        parts.append(level_key)
        parts.append(" = ")
    return "deep = " + "".join(parts) + leaf + ("}" * depth)


@composite
def deep_dotted_document(draw):
    depth = draw(st.integers(min_value=90001, max_value=120000))
    quoted = draw(st.booleans())
    if quoted:
        parts = [
            '"q"' if i % 2 else "'l'"
            for i in range(depth)
        ]
    else:
        parts = [
            "a" if i % 2 else "b"
            for i in range(depth)
        ]
    leaf = draw(
        st.one_of(
            integer_value,
            boolean_value,
            basic_string,
            floating_value,
        )
    )
    return "deep." + ".".join(parts) + " = " + leaf


@composite
def many_siblings_document(draw):
    count = draw(st.integers(min_value=30001, max_value=45000))
    prefix = draw(st.sampled_from(["k", "key", "sibling"]))
    mode = draw(st.integers(min_value=0, max_value=4))
    lines = ["[many_siblings]"]
    for i in range(count):
        if mode == 0:
            item = "true" if i % 3 == 0 else "false"
        elif mode == 1:
            item = str(i)
        elif mode == 2:
            item = f'"value-{i}"'
        elif mode == 3:
            item = f"{i}.000000001"
        else:
            item = f"0x{i:x}"
        lines.append(f"{prefix}{i} = {item}")
    return "\n".join(lines)


@composite
def long_flat_document(draw):
    count = draw(st.integers(min_value=26001, max_value=42000))
    prefix = draw(st.sampled_from(["line", "entry", "field"]))
    lines = []
    for i in range(count):
        if i % 5 == 0:
            value_text = "true"
        elif i % 5 == 1:
            value_text = str(i)
        elif i % 5 == 2:
            value_text = f'"v{i}"'
        elif i % 5 == 3:
            value_text = f"[{i}, {i + 1},]"
        else:
            value_text = f"0x{i:x}"
        lines.append(
            f"{prefix}{i} = {value_text} # line {i}"
        )
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 16),
    *([unique_pair_document()] * 5),
    biased_document(),
    duplicate_document(),
    deep_array_document(),
    deep_inline_document(),
    deep_dotted_document(),
    many_siblings_document(),
    long_flat_document(),
)