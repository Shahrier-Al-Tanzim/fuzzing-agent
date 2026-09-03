"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-09-02T21:58:28.251024+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " -_./:@"
)
SAFE_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " -_./:@\\"
)
HEX = "0123456789abcdefABCDEF"
DIGITS = "0123456789"


def _join(parts, sep=""):
    return sep.join(parts)


unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8)
quoted_basic_key = st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=8).map(lambda s: '"' + s + '"')
quoted_literal_key = st.text(alphabet=SAFE_LITERAL_CHARS.replace("'", ""), min_size=1, max_size=8).map(lambda s: "'" + s + "'")
simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key, min_size=2, max_size=4))
    return ".".join(parts)


key_strategy = st.one_of(simple_key, dotted_key())


escaped_string = st.sampled_from([
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
])

literal_string = st.sampled_from([
    "''",
    "'simple'",
    "'literal \\\\ path'",
    "'no escapes here'",
])

ml_basic_string = st.sampled_from([
    '""""""',
    '"""multi"""',
    '"""line1\nline2"""',
    '"""a\\\n b"""',
])

ml_literal_string = st.sampled_from([
    "''''''",
    "'''multi'''",
    "'''line1\nline2'''",
])

string_value = st.one_of(escaped_string, literal_string, ml_basic_string, ml_literal_string)

int_value = st.sampled_from([
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
    "007",
    "0x0",
    "0xDEAD_BEEF",
    "0o755",
    "0b1010_0101",
])

float_value = st.sampled_from([
    "0.0",
    "-0.0",
    "1e6",
    "-2E-3",
    "6.022e23",
    "1_2.3_4",
    "inf",
    "-inf",
    "nan",
])

bool_value = st.sampled_from(["true", "false"])

date_value = st.sampled_from([
    "1979-05-27T07:32:00Z",
    "1979-05-27T00:32:00-07:00",
    "1979-05-27 00:32:00.9999999999999999999",
    "1979-05-27T00:32:00.9999999999999999999-07:00",
    "1979-05-27T00:32:00",
    "1979-05-27",
    "07:32:00",
    "00:32:00.9999999999999999999",
])

scalar_value = st.one_of(string_value, int_value, float_value, bool_value, date_value)


def _inline_table_from_pairs(pairs, trailing=False):
    if not pairs:
        return "{}"
    body = ", ".join([k + " = " + v for k, v in pairs])
    if trailing:
        body += ","
    return "{ " + body + " }"


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
        pair_list(children, min_size=0, max_size=4, unique_keys=True).map(
            lambda pairs: _inline_table_from_pairs(pairs, trailing=False)
        ),
        pair_list(children, min_size=1, max_size=4, unique_keys=True).map(
            lambda pairs: _inline_table_from_pairs(pairs, trailing=True)
        ),
    ),
    max_leaves=30,
)


@composite
def key_value_line(draw):
    k = draw(key_strategy)
    v = draw(recursive_value)
    c = draw(st.sampled_from(["", "", "", " # c", " # edge"]))
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
        )))
    return "\n".join(parts)


@composite
def deep_array_value(draw):
    n = draw(st.integers(min_value=200, max_value=1200))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table_value(draw):
    n = draw(st.integers(min_value=150, max_value=700))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=300, max_value=1500))
    return ("a." * n) + "k = 1"


@composite
def deep_mixed_value(draw):
    n = draw(st.integers(min_value=120, max_value=500))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed_value(draw):
    n = draw(st.integers(min_value=100, max_value=350))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc_from_value(draw, value_strategy):
    k = draw(simple_key)
    v = draw(value_strategy)
    return k + " = " + v


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=2000, max_value=12000))
    lines = ["[a]"]
    for i in range(n):
        lines.append("k" + str(i) + " = 1")
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([ordinary_document()] * 24),
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