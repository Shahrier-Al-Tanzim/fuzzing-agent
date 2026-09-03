"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-02T21:32:10.199321+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
NON_ASCII_CHARS = "éßø中🙂ΩЖñçüαβγд"
SAFE_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " _-./:+@" + NON_ASCII_CHARS
)
SAFE_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " _-./:+@\\"
    + NON_ASCII_CHARS
)
HEX = "0123456789abcdefABCDEF"


def _join(xs, sep):
    return sep.join(xs)


def _pad2(n):
    return f"{n:02d}"


def _pad4(n):
    return f"{n:04d}"


unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12
)

basic_key = st.text(
    alphabet=SAFE_BASIC_CHARS.replace('"', "").replace("\\", "").replace("\n", "").replace("\r", ""),
    min_size=1,
    max_size=12,
).map(lambda s: '"' + s + '"')

literal_key = st.text(
    alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\n", "").replace("\r", ""),
    min_size=1,
    max_size=12,
).map(lambda s: "'" + s + "'")

simple_key = st.one_of(
    unquoted_key,
    unquoted_key,
    unquoted_key,
    basic_key,
    literal_key,
)

dotted_key = st.lists(simple_key, min_size=2, max_size=5).map(lambda parts: _join(parts, "."))

key_strategy = st.one_of(
    simple_key,
    simple_key,
    simple_key,
    dotted_key,
)

escaped_piece = st.one_of(
    st.just("\\n"),
    st.just("\\t"),
    st.just('\\"'),
    st.just("\\\\"),
    st.text(alphabet=HEX, min_size=4, max_size=4).map(lambda h: "\\u" + h),
    st.text(alphabet=HEX, min_size=8, max_size=8).map(lambda h: "\\U" + h),
)

plain_basic_piece = st.text(
    alphabet=SAFE_BASIC_CHARS.replace('"', "").replace("\\", "").replace("\n", "").replace("\r", ""),
    min_size=0,
    max_size=8,
)

basic_string = st.lists(
    st.one_of(plain_basic_piece, escaped_piece),
    min_size=0,
    max_size=6,
).map(lambda parts: '"' + "".join(parts) + '"')

literal_string = st.text(
    alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\n", "").replace("\r", ""),
    min_size=0,
    max_size=24,
).map(lambda s: "'" + s + "'")

ml_basic_piece = st.one_of(
    st.text(
        alphabet=SAFE_BASIC_CHARS.replace("\\", "").replace("\r", "") + "\n",
        min_size=0,
        max_size=8,
    ),
    escaped_piece,
    st.just("\\\n"),
)

ml_basic_string = st.lists(ml_basic_piece, min_size=0, max_size=8).map(
    lambda parts: '"""' + "".join(parts).replace('"""', '""') + '"""'
)

ml_literal_string = st.text(
    alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\r", "") + "\n",
    min_size=0,
    max_size=24,
).map(lambda s: "'''" + s.replace("'''", "''") + "'''")

valid_string = st.one_of(
    basic_string,
    basic_string,
    literal_string,
    ml_basic_string,
    ml_basic_string,
    ml_basic_string,
    ml_literal_string,
)

invalid_escape_string = st.text(
    alphabet="qxyz",
    min_size=1,
    max_size=4,
).map(lambda s: '"\\' + s + '"')

dec_small = st.integers(min_value=-1000000, max_value=1000000).map(str)
dec_extreme = st.sampled_from([
    "0",
    "-0",
    "9223372036854775807",
    "-9223372036854775808",
    "9223372036854775808",
    "-9223372036854775809",
])
leading_zero_int = st.sampled_from(["007", "00", "-00", "0001", "0123"])
underscored_dec = st.sampled_from([
    "1_000",
    "9_223_372_036_854_775_807",
    "10_0",
    "5_4_3_2_1",
])
hex_int = st.sampled_from(["0x0", "0x1", "0xdeadBEEF", "0x7fff_ffff"])
oct_int = st.sampled_from(["0o0", "0o7", "0o755", "0o1_2_3"])
bin_int = st.sampled_from(["0b0", "0b1", "0b1010", "0b1111_0000"])
integer_value = st.one_of(
    dec_small,
    dec_small,
    dec_extreme,
    leading_zero_int,
    underscored_dec,
    hex_int,
    oct_int,
    bin_int,
)

float_value = st.one_of(
    st.sampled_from([
        "0.0",
        "-0.0",
        "1e6",
        "-2E-3",
        "6.022e23",
        "1_2.3_4",
        "3.1415",
        "9e999",
        "inf",
        "-inf",
        "+inf",
        "nan",
        "+nan",
        "-nan",
    ]),
    st.tuples(
        st.integers(min_value=-1000, max_value=1000),
        st.integers(min_value=0, max_value=999999),
        st.integers(min_value=-20, max_value=20),
    ).map(lambda t: f"{t[0]}.{t[1]}e{t[2]}"),
)

boolean_value = st.sampled_from(["true", "false"])

local_date = st.tuples(
    st.integers(min_value=1970, max_value=2100),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28),
).map(lambda t: f"{_pad4(t[0])}-{_pad2(t[1])}-{_pad2(t[2])}")

local_time_plain = st.tuples(
    st.integers(min_value=0, max_value=23),
    st.integers(min_value=0, max_value=59),
    st.integers(min_value=0, max_value=59),
).map(lambda t: f"{_pad2(t[0])}:{_pad2(t[1])}:{_pad2(t[2])}")

local_time_frac = st.tuples(
    st.integers(min_value=0, max_value=23),
    st.integers(min_value=0, max_value=59),
    st.integers(min_value=0, max_value=59),
    st.one_of(
        st.integers(min_value=0, max_value=9999999999999999999).map(
            lambda n: "." + str(n).rjust(19, "0")
        ),
        st.integers(min_value=0, max_value=999999).map(
            lambda n: "." + str(n).rjust(6, "0")
        ),
    ),
).map(lambda t: f"{_pad2(t[0])}:{_pad2(t[1])}:{_pad2(t[2])}{t[3]}")

local_time = st.one_of(
    local_time_plain,
    local_time_plain,
    local_time_plain,
    local_time_frac,
)

offset = st.one_of(
    st.just("Z"),
    st.tuples(
        st.sampled_from(["+", "-"]),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
    ).map(lambda t: f"{t[0]}{_pad2(t[1])}:{_pad2(t[2])}"),
)

offset_date_time = st.tuples(local_date, local_time, offset).map(
    lambda t: f"{t[0]}T{t[1]}{t[2]}"
)
local_date_time = st.tuples(local_date, local_time).map(lambda t: f"{t[0]} {t[1]}")

date_time_value = st.one_of(
    offset_date_time,
    local_date_time,
    local_date,
    local_date,
    local_time,
    local_time,
)


@composite
def inline_table_pairs(draw, value_strategy, allow_trailing):
    n = draw(st.integers(min_value=1, max_value=4))
    parts = []
    for _ in range(n):
        k = draw(key_strategy)
        v = draw(value_strategy)
        parts.append(f"{k} = {v}")
    if draw(st.booleans()):
        dupk = draw(key_strategy)
        dupv1 = draw(value_strategy)
        dupv2 = draw(value_strategy)
        parts.append(f"{dupk} = {dupv1}")
        parts.append(f"{dupk} = {dupv2}")
    body = ", ".join(parts)
    if allow_trailing and draw(st.booleans()):
        body = body + ","
    return body


scalar_value = st.one_of(
    valid_string,
    valid_string,
    valid_string,
    integer_value,
    integer_value,
    float_value,
    float_value,
    boolean_value,
    date_time_value,
    date_time_value,
)

container_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(children, min_size=0, max_size=4).map(lambda xs: "[" + ", ".join(xs) + "]"),
        inline_table_pairs(children, allow_trailing=False).map(lambda body: "{" + body + "}"),
        st.just("[]"),
        st.just("{}"),
    ),
    max_leaves=30,
)

biased_container_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(children, min_size=1, max_size=1).map(lambda xs: "[" + ", ".join(xs) + "]"),
        st.lists(children, min_size=1, max_size=1).map(lambda xs: "[" + ", ".join(xs) + "]"),
        st.lists(children, min_size=1, max_size=1).map(lambda xs: "[" + ", ".join(xs) + "]"),
        inline_table_pairs(children, allow_trailing=False).map(lambda body: "{" + body + "}"),
        inline_table_pairs(children, allow_trailing=False).map(lambda body: "{" + body + "}"),
        st.just("[]"),
        st.just("{}"),
    ),
    max_leaves=40,
)


@composite
def key_value_line(draw, value_strategy=container_value):
    k = draw(key_strategy)
    v = draw(value_strategy)
    line = f"{k} = {v}"
    if draw(st.integers(min_value=0, max_value=4)) == 0:
        c = draw(st.text(alphabet=SAFE_BASIC_CHARS.replace("\n", "").replace("\r", ""), min_size=0, max_size=12))
        line = line + " #" + c
    return line


@composite
def duplicate_key_lines(draw, value_strategy=container_value):
    k = draw(key_strategy)
    v1 = draw(value_strategy)
    v2 = draw(value_strategy)
    return f"{k} = {v1}\n{k} = {v2}"


@composite
def standard_table_block(draw, value_strategy=container_value):
    header = "[" + draw(key_strategy) + "]"
    n = draw(st.integers(min_value=0, max_value=4))
    lines = [header]
    for _ in range(n):
        lines.append(draw(key_value_line(value_strategy)))
    if draw(st.booleans()):
        lines.append(draw(duplicate_key_lines(value_strategy)))
    return "\n".join(lines)


@composite
def array_table_block(draw, value_strategy=container_value):
    header = "[[" + draw(key_strategy) + "]]"
    n = draw(st.integers(min_value=0, max_value=4))
    lines = [header]
    for _ in range(n):
        lines.append(draw(key_value_line(value_strategy)))
    return "\n".join(lines)


@composite
def valid_document(draw, value_strategy=container_value):
    n = draw(st.integers(min_value=1, max_value=8))
    parts = []
    for _ in range(n):
        parts.append(draw(st.one_of(
            key_value_line(value_strategy),
            key_value_line(value_strategy),
            key_value_line(value_strategy),
            standard_table_block(value_strategy),
            array_table_block(value_strategy),
        )))
    return "\n".join(parts)


@composite
def priority_document(draw):
    choice = draw(st.integers(min_value=0, max_value=9))
    if choice == 0:
        return 'x = """hello\nworld"""'
    if choice == 1:
        return 'x = """é\n中\n🙂"""'
    if choice == 2:
        return 'é = "中🙂Ω"'
    if choice == 3:
        return 'x = +inf'
    if choice == 4:
        return 'x = -inf'
    if choice == 5:
        return 'x = inf'
    if choice == 6:
        return "x = 1979-05-27"
    if choice == 7:
        return "x = 00:32:00"
    if choice == 8:
        return "x = 00:32:00.9999999999999999999"
    return draw(valid_document(container_value))


@composite
def divergence_document(draw):
    choice = draw(st.integers(min_value=0, max_value=8))
    if choice == 0:
        return 'x = { a = 1, b = 2, }'
    if choice == 1:
        frac = draw(st.integers(min_value=10**18, max_value=10**19 - 1)).__str__()
        return "x = 1979-05-27T00:32:00." + frac + "-07:00"
    if choice == 2:
        return "x = 9223372036854775808"
    if choice == 3:
        return "x = 007"
    if choice == 4:
        return draw(duplicate_key_lines(container_value))
    if choice == 5:
        body = draw(inline_table_pairs(container_value, allow_trailing=True))
        return "x = {" + body + "}"
    if choice == 6:
        return "x = []\ny = {}\n"
    if choice == 7:
        return 'x = """é\n中\n🙂"""'
    return "x = 00:32:00"

@composite
def malformed_document(draw):
    choice = draw(st.integers(min_value=0, max_value=7))
    if choice == 0:
        return "x = { a = 1,\n b = 2 }"
    if choice == 1:
        return "x 1"
    if choice == 2:
        return "x = [1, 2"
    if choice == 3:
        return 'x = "unterminated'
    if choice == 4:
        return "x = { a = 1, b = 2, }"
    if choice == 5:
        return "x = " + draw(invalid_escape_string)
    if choice == 6:
        return "[a\nx = 1"
    return "x = '''abc"


@composite
def deep_array_value(draw):
    n = draw(st.integers(min_value=200, max_value=4000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table_value(draw):
    n = draw(st.integers(min_value=200, max_value=4000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_mixed_value(draw):
    n = draw(st.integers(min_value=150, max_value=2500))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed_value(draw):
    n = draw(st.integers(min_value=120, max_value=1800))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc(draw, value_builder):
    k = draw(simple_key)
    v = draw(value_builder())
    return f"{k} = {v}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=200, max_value=3000))
    lines = ["[a]"]
    for i in range(n):
        lines.append(f"k{i} = 1")
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([valid_document(container_value)] * 12),
    *([valid_document(biased_container_value)] * 6),
    *([priority_document()] * 8),
    *([divergence_document()] * 3),
    *([malformed_document()] * 2),
    deep_doc(deep_array_value),
    deep_doc(deep_inline_table_value),
    deep_doc(deep_mixed_value),
    deep_doc(deep_quoted_mixed_value),
    many_siblings(),
)