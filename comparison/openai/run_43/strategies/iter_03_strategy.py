"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-09-02T22:01:52.375783+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " -_./:@"
    "éΩ中ßµñøключïáç"
)
SAFE_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " -_./:@\\"
    "éΩ中ßµñøключïáç"
)
SAFE_COMMENT_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " -_./:@"
    "éΩ中ßµñøключïáç"
)
HEX = "0123456789abcdefABCDEF"
DIGITS = "0123456789"


def _join(parts, sep=""):
    return sep.join(parts)


def _inline_table_from_pairs(pairs, trailing=False):
    if not pairs:
        return "{}"
    body = ", ".join([k + " = " + v for k, v in pairs])
    if trailing:
        body += ","
    return "{ " + body + " }"


def _array_from_values(values, multiline=False, with_comments=False, trailing=False):
    if not values:
        return "[]"
    if not multiline:
        body = ", ".join(values)
        if trailing:
            body += ","
        return "[" + body + "]"
    pieces = ["["]
    for i, v in enumerate(values):
        line = "  " + v
        if with_comments and i % 2 == 0:
            line += " # arr"
        if i != len(values) - 1 or trailing:
            line += ","
        pieces.append(line)
    pieces.append("]")
    return "\n".join(pieces)


def _comment_suffixes():
    return st.sampled_from([
        "",
        "",
        "",
        " # c",
        " # edge",
        " # é",
        " # Ω中",
        " # naïve café",
        " # ключ",
    ])


unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8)
quoted_basic_key = st.text(
    alphabet=SAFE_BASIC_CHARS.replace('"', "").replace("\\", "").replace("\n", "").replace("\r", ""),
    min_size=1,
    max_size=8,
).map(lambda s: '"' + s + '"')
quoted_literal_key = st.text(
    alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\n", "").replace("\r", ""),
    min_size=1,
    max_size=8,
).map(lambda s: "'" + s + "'")
simple_key = st.one_of(
    unquoted_key,
    quoted_basic_key,
    quoted_literal_key,
    st.sampled_from(['"é"', '"Ω"', '"中"', '"ключ"', '"naïve"', "'é'", "'Ω'", "'中'"]),
)


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key, min_size=2, max_size=4))
    return ".".join(parts)


key_strategy = st.one_of(simple_key, dotted_key())

escaped_string = st.one_of(
    st.sampled_from([
        '""',
        '"simple"',
        '"with space"',
        '"\\\\n"',
        '"\\\\t"',
        '"\\\\\\""',
        '"\\\\\\\\"',
        '"\\\\u0041"',
        '"\\\\U0001F600"',
        '"mix \\\\n \\\\t \\\\u03A9"',
        '"999999999999999999999999999999"',
        '"-9223372036854775809"',
    ]),
    st.text(
        alphabet=SAFE_BASIC_CHARS.replace('"', "").replace("\\", "").replace("\n", "").replace("\r", ""),
        min_size=0,
        max_size=24,
    ).map(lambda s: '"' + s + '"'),
    st.sampled_from([
        '"é"',
        '"Ω"',
        '"中"',
        '"naïve café"',
        '"ключ"',
        '"mañana"',
        '"µßø"',
    ]),
)

literal_string = st.one_of(
    st.sampled_from([
        "''",
        "'simple'",
        "'literal \\\\ path'",
        "'no escapes here'",
        "'007'",
        "'9223372036854775808'",
    ]),
    st.text(
        alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\n", "").replace("\r", ""),
        min_size=0,
        max_size=24,
    ).map(lambda s: "'" + s + "'"),
    st.sampled_from([
        "'é'",
        "'Ω'",
        "'中'",
        "'naïve café'",
        "'ключ'",
        "'mañana'",
        "'µßø'",
    ]),
)

ml_basic_string = st.one_of(
    st.sampled_from([
        '""""""',
        '"""multi"""',
        '"""line1\nline2"""',
        '"""a\\\n b"""',
        '"""é\nΩ\n中"""',
        '"""1979-05-27T00:32:00.9999999999999999999-07:00\n9223372036854775808"""',
    ]),
    st.text(
        alphabet=SAFE_BASIC_CHARS.replace('"', "").replace("\\", "").replace("\r", ""),
        min_size=0,
        max_size=32,
    ).map(lambda s: '"""' + s.replace("\n\n\n", "\n") + '"""'),
)

ml_literal_string = st.one_of(
    st.sampled_from([
        "''''''",
        "'''multi'''",
        "'''line1\nline2'''",
        "'''é\nΩ\n中'''",
        "'''007\n0001\n-007'''",
    ]),
    st.text(
        alphabet=SAFE_LITERAL_CHARS.replace("'", "").replace("\r", ""),
        min_size=0,
        max_size=32,
    ).map(lambda s: "'''" + s.replace("\n\n\n", "\n") + "'''"),
)

string_value = st.one_of(escaped_string, literal_string, ml_basic_string, ml_literal_string)

int_value = st.one_of(
    st.sampled_from([
        "0",
        "-0",
        "1",
        "-1",
        "7",
        "42",
        "1_000",
        "9_223_372_036_854_775_807",
        "-9_223_372_036_854_775_808",
        "9223372036854775808",
        "-9223372036854775809",
        "18446744073709551615",
        "-18446744073709551616",
        "007",
        "0001",
        "-007",
        "0x0",
        "0xDEAD_BEEF",
        "0x7fff_ffff_ffff_ffff",
        "0o755",
        "0o7_7_7_7_7",
        "0b1010_0101",
        "0b1111111111111111111111111111111111111111111111111111111111111111",
    ]),
    st.integers(min_value=0, max_value=10**24).map(str),
    st.integers(min_value=10**18, max_value=10**24).map(lambda n: "-" + str(n)),
)

float_value = st.one_of(
    st.sampled_from([
        "0.0",
        "-0.0",
        "1e6",
        "-2E-3",
        "6.022e23",
        "1_2.3_4",
        "inf",
        "-inf",
        "nan",
        "+inf",
        "+nan",
        "9223372036854775808.0",
        "0.0000000000000000000000001",
        "1e999",
        "-1e999",
    ]),
    st.tuples(
        st.integers(min_value=0, max_value=10**12),
        st.integers(min_value=0, max_value=10**12),
        st.integers(min_value=-400, max_value=400),
    ).map(lambda t: str(t[0]) + "." + str(t[1]) + "e" + str(t[2])),
)

bool_value = st.sampled_from(["true", "false"])

date_value = st.one_of(
    st.sampled_from([
        "1979-05-27T07:32:00Z",
        "1979-05-27T00:32:00-07:00",
        "1979-05-27 00:32:00.9999999999999999999",
        "1979-05-27T00:32:00.9999999999999999999-07:00",
        "1979-05-27T00:32:00",
        "1979-05-27",
        "07:32:00",
        "00:32:00.9999999999999999999",
        "0001-01-01T00:00:00Z",
        "9999-12-31T23:59:59.9999999999999999999+23:59",
    ]),
    st.tuples(
        st.integers(min_value=1, max_value=9999),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
    st.tuples(
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=7, max_value=24),
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}." + ("9" * t[3])),
)

scalar_value = st.one_of(string_value, int_value, float_value, bool_value, date_value)


@composite
def pair_list(draw, value_strategy, min_size=1, max_size=4, unique_keys=True):
    keys = draw(st.lists(simple_key, min_size=min_size, max_size=max_size, unique=unique_keys))
    vals = draw(st.lists(value_strategy, min_size=len(keys), max_size=len(keys)))
    out = []
    for i in range(len(keys)):
        out.append((keys[i], vals[i]))
    return out


recursive_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(
            st.one_of(children, children, children),
            min_size=0,
            max_size=4,
        ).map(lambda xs: "[" + ", ".join(xs) + "]"),
        st.lists(
            st.one_of(children, children, children),
            min_size=0,
            max_size=4,
        ).map(lambda xs: _array_from_values(xs, multiline=True, with_comments=False, trailing=False)),
        st.lists(
            st.one_of(children, children, children),
            min_size=1,
            max_size=4,
        ).map(lambda xs: _array_from_values(xs, multiline=True, with_comments=True, trailing=True)),
        pair_list(children, min_size=0, max_size=4, unique_keys=True).map(
            lambda pairs: _inline_table_from_pairs(pairs, trailing=False)
        ),
        pair_list(children, min_size=1, max_size=4, unique_keys=True).map(
            lambda pairs: _inline_table_from_pairs(pairs, trailing=True)
        ),
    ),
    max_leaves=36,
)


@composite
def rare_extreme_scalar(draw):
    return draw(st.one_of(
        st.sampled_from([
            "9223372036854775808",
            "-9223372036854775809",
            "007",
            "0001",
            "-007",
            "1979-05-27T00:32:00.9999999999999999999-07:00",
            "1979-05-27 00:32:00.9999999999999999999",
            "00:32:00.9999999999999999999",
            '"\\\\U0001F600"',
            '"""1979-05-27T00:32:00.9999999999999999999\n9223372036854775808\n007"""',
            "1e999",
            "-1e999",
            "nan",
            "-inf",
        ]),
        scalar_value,
    ))


@composite
def nested_extreme_value(draw, depth=0):
    if depth >= 8:
        return draw(rare_extreme_scalar())

    if depth < 5:
        return draw(st.one_of(
            nested_extreme_array(depth=depth + 1),
            nested_extreme_array(depth=depth + 1),
            nested_extreme_array(depth=depth + 1),
            nested_extreme_inline_table(depth=depth + 1),
            nested_extreme_inline_table(depth=depth + 1),
            nested_extreme_inline_table(depth=depth + 1),
            rare_extreme_scalar(),
        ))

    return draw(st.one_of(
        nested_extreme_array(depth=depth + 1),
        nested_extreme_inline_table(depth=depth + 1),
        rare_extreme_scalar(),
        rare_extreme_scalar(),
    ))


@composite
def nested_extreme_array(draw, depth=0):
    if depth >= 8:
        xs = [draw(rare_extreme_scalar())]
        return _array_from_values(xs, multiline=False, trailing=False)

    n = draw(st.integers(min_value=1, max_value=3))
    values = []
    for _ in range(n):
        values.append(draw(st.one_of(
            nested_extreme_value(depth=depth + 1),
            nested_extreme_value(depth=depth + 1),
            rare_extreme_scalar(),
        )))
    multiline = draw(st.booleans())
    with_comments = draw(st.booleans())
    trailing = draw(st.booleans())
    return _array_from_values(values, multiline=multiline, with_comments=with_comments, trailing=trailing)


@composite
def nested_extreme_inline_table(draw, depth=0):
    if depth >= 8:
        k = draw(simple_key)
        return _inline_table_from_pairs([(k, draw(rare_extreme_scalar()))], trailing=True)

    n = draw(st.integers(min_value=1, max_value=3))
    pairs = []
    seen = set()
    for _ in range(n):
        k = draw(simple_key)
        while k in seen:
            k = draw(simple_key)
        seen.add(k)
        v = draw(st.one_of(
            nested_extreme_value(depth=depth + 1),
            nested_extreme_value(depth=depth + 1),
            rare_extreme_scalar(),
        ))
        pairs.append((k, v))
    trailing = draw(st.booleans())
    return _inline_table_from_pairs(pairs, trailing=trailing)


@composite
def depth_biased_value(draw, depth=0):
    if depth >= 4500:
        return draw(scalar_value)

    if depth < 4000:
        return draw(st.one_of(
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_value(depth=depth + 1),
            depth_biased_array(depth=depth + 1),
            depth_biased_array(depth=depth + 1),
            depth_biased_array(depth=depth + 1),
            depth_biased_inline_table(depth=depth + 1),
            depth_biased_inline_table(depth=depth + 1),
            scalar_value,
        ))

    return draw(st.one_of(
        depth_biased_array(depth=depth + 1),
        depth_biased_array(depth=depth + 1),
        depth_biased_inline_table(depth=depth + 1),
        scalar_value,
        scalar_value,
    ))


@composite
def depth_biased_array(draw, depth=0):
    if depth >= 4500:
        return "[" + draw(scalar_value) + "]"
    child = draw(st.one_of(
        depth_biased_value(depth=depth + 1),
        depth_biased_array(depth=depth + 1),
        depth_biased_array(depth=depth + 1),
        depth_biased_inline_table(depth=depth + 1),
    ))
    return "[" + child + "]"


@composite
def depth_biased_inline_table(draw, depth=0):
    if depth >= 4500:
        return "{ a = " + draw(scalar_value) + " }"
    child = draw(st.one_of(
        depth_biased_value(depth=depth + 1),
        depth_biased_array(depth=depth + 1),
        depth_biased_inline_table(depth=depth + 1),
        depth_biased_inline_table(depth=depth + 1),
    ))
    k = draw(simple_key)
    trailing = draw(st.booleans())
    return _inline_table_from_pairs([(k, child)], trailing=trailing)


@composite
def key_value_line(draw):
    k = draw(key_strategy)
    v = draw(recursive_value)
    c = draw(_comment_suffixes())
    return k + " = " + v + c


@composite
def depth_biased_key_value_line(draw):
    k = draw(key_strategy)
    v = draw(depth_biased_value())
    c = draw(st.sampled_from([
        "",
        "",
        " # deep",
        " # Ω",
    ]))
    return k + " = " + v + c


@composite
def extreme_nested_key_value_line(draw):
    k = draw(key_strategy)
    v = draw(nested_extreme_value())
    c = draw(st.sampled_from([
        "",
        "",
        " # extreme",
        " # trunc",
        " # overflow",
        " # leading-zero",
    ]))
    return k + " = " + v + c


@composite
def duplicate_top_level_doc(draw):
    k = draw(simple_key)
    v1 = draw(scalar_value)
    v2 = draw(recursive_value)
    return k + " = " + v1 + "\n" + k + " = " + v2


@composite
def inline_table_duplicate_doc(draw):
    outer = draw(simple_key)
    inner = draw(simple_key)
    v1 = draw(scalar_value)
    v2 = draw(scalar_value)
    return outer + " = { " + inner + " = " + v1 + ", " + inner + " = " + v2 + " }"


@composite
def duplicate_key_accepted_doc(draw):
    table = draw(simple_key)
    key = draw(simple_key)
    v1 = draw(scalar_value)
    v2 = draw(recursive_value)
    return "[[" + table + "]]\n" + key + " = " + v1 + "\n[[" + table + "]]\n" + key + " = " + v2


@composite
def duplicate_key_mixed_doc(draw):
    table = draw(key_strategy)
    key1 = draw(simple_key)
    key2 = draw(simple_key)
    v1 = draw(recursive_value)
    v2 = draw(recursive_value)
    v3 = draw(recursive_value)
    return (
        "[[" + table + "]]\n" +
        key1 + " = " + v1 + "\n" +
        key2 + " = " + v2 + "\n" +
        "[[" + table + "]]\n" +
        key1 + " = " + v3
    )


@composite
def standard_table_block(draw):
    header = draw(key_strategy)
    n = draw(st.integers(min_value=0, max_value=4))
    lines = []
    seen = set()
    for _ in range(n):
        k = draw(simple_key)
        while k in seen:
            k = draw(simple_key)
        seen.add(k)
        v = draw(recursive_value)
        lines.append(k + " = " + v)
    if lines:
        return "[" + header + "]\n" + "\n".join(lines)
    return "[" + header + "]"


@composite
def array_table_block(draw):
    header = draw(key_strategy)
    n = draw(st.integers(min_value=0, max_value=4))
    lines = []
    seen = set()
    for _ in range(n):
        k = draw(simple_key)
        while k in seen:
            k = draw(simple_key)
        seen.add(k)
        v = draw(recursive_value)
        lines.append(k + " = " + v)
    if lines:
        return "[[" + header + "]]\n" + "\n".join(lines)
    return "[[" + header + "]]"


@composite
def extreme_array_table_block(draw):
    header = draw(key_strategy)
    n = draw(st.integers(min_value=1, max_value=3))
    lines = []
    seen = set()
    for _ in range(n):
        k = draw(simple_key)
        while k in seen:
            k = draw(simple_key)
        seen.add(k)
        v = draw(nested_extreme_value())
        lines.append(k + " = " + v)
    return "[[" + header + "]]\n" + "\n".join(lines)


@composite
def deep_array_table_chain_doc(draw):
    outer = draw(simple_key)
    inner = draw(simple_key)
    leaf = draw(simple_key)
    v = draw(nested_extreme_inline_table(depth=2))
    return (
        "[[" + outer + "]]\n"
        + inner + " = [\n"
        + "  { " + leaf + " = " + v + ", },\n"
        + "]"
    )


@composite
def non_ascii_doc(draw):
    top = draw(st.sampled_from([
        '"é"', '"Ω"', '"中"', '"ключ"', '"naïve"', "'é'", "'Ω'", "'中'"
    ]))
    inner = draw(st.sampled_from([
        '"é"', '"Ω"', '"中"', '"ключ"', '"naïve"', "'é'", "'Ω'", "'中'"
    ]))
    value = draw(st.one_of(
        st.sampled_from([
            '"é"', '"Ω"', '"中"', '"naïve café"', '"ключ"',
            "'é'", "'Ω'", "'中'", "'naïve café'", "'ключ'",
            '"""é\nΩ\n中"""',
            "'''é\nΩ\n中'''",
        ]),
        recursive_value,
    ))
    return top + " = { " + inner + " = " + value + ", } # Ω"


@composite
def malformed_doc(draw):
    k = draw(simple_key)
    v = draw(scalar_value)
    return draw(st.one_of(
        st.just(k + " " + v),
        st.just(k + " = { a = 1,\n b = 2 }"),
        st.just(k + " = [1, 2"),
        st.just("[" + k),
        st.just(k + " = " + '"unterminated'),
        st.just(k + " = " + "'unterminated"),
        st.just(k + " = " + '"\\q"'),
    ))


@composite
def ordinary_document(draw):
    count = draw(st.integers(min_value=0, max_value=6))
    parts = []
    for _ in range(count):
        parts.append(draw(st.one_of(
            key_value_line(),
            key_value_line(),
            standard_table_block(),
            array_table_block(),
            non_ascii_doc(),
        )))
    return "\n".join(parts)


@composite
def depth_biased_document(draw):
    count = draw(st.integers(min_value=1, max_value=3))
    parts = []
    for _ in range(count):
        parts.append(draw(st.one_of(
            depth_biased_key_value_line(),
            depth_biased_key_value_line(),
            standard_table_block(),
            array_table_block(),
        )))
    return "\n".join(parts)


@composite
def extreme_nested_document(draw):
    count = draw(st.integers(min_value=1, max_value=4))
    parts = []
    for _ in range(count):
        parts.append(draw(st.one_of(
            extreme_nested_key_value_line(),
            extreme_nested_key_value_line(),
            extreme_array_table_block(),
            deep_array_table_chain_doc(),
            standard_table_block(),
        )))
    return "\n".join(parts)


@composite
def deep_array_value(draw):
    n = draw(st.integers(min_value=60000, max_value=100000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table_value(draw):
    n = draw(st.integers(min_value=85000, max_value=115000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100000, max_value=130000))
    return ("a." * n) + "k = 1"


@composite
def deep_mixed_value(draw):
    n = draw(st.integers(min_value=60000, max_value=80000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed_value(draw):
    n = draw(st.integers(min_value=20000, max_value=45000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc_from_value(draw, value_strategy):
    k = draw(simple_key)
    v = draw(value_strategy)
    return k + " = " + v


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    lines = ["[a]"]
    for i in range(n):
        lines.append("k" + str(i) + " = 1")
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 20),
    *([depth_biased_document()] * 6),
    *([extreme_nested_document()] * 8),
    *([non_ascii_doc()] * 6),
    *([duplicate_key_accepted_doc()] * 6),
    *([duplicate_key_mixed_doc()] * 4),
    duplicate_top_level_doc(),
    inline_table_duplicate_doc(),
    malformed_doc(),
    deep_doc_from_value(deep_array_value()),
    deep_doc_from_value(deep_inline_table_value()),
    deep_dotted_key_doc(),
    deep_doc_from_value(deep_mixed_value()),
    deep_doc_from_value(deep_quoted_mixed_value()),
    many_siblings(),
)