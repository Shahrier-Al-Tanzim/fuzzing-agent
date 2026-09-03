"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-09-02T22:09:44.489119+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " _-./:"
)
SAFE_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " _-./:\\"
)
NON_ASCII_CHARS = "αβγδεζηθλμνοπρστυφχψωéñüçøå中日文猫😀"


def _join(parts, sep=""):
    return sep.join(parts)


def _pad2(n):
    return f"{n:02d}"


def _pad4(n):
    return f"{n:04d}"


unquoted_key = st.text(
    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8
)

safe_basic_inner = st.text(
    alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=16
).map(lambda s: '"' + s + '"')

safe_literal_inner = st.text(
    alphabet=SAFE_LITERAL_CHARS.replace("'", ""), min_size=0, max_size=16
).map(lambda s: "'" + s + "'")

non_ascii_basic_string = st.one_of(
    st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=8).map(lambda s: '"' + s + '"'),
    st.tuples(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=6),
        st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=4),
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=6),
    ).map(lambda t: '"' + t[0] + t[1] + t[2] + '"'),
)

non_ascii_literal_string = st.one_of(
    st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=8).map(lambda s: "'" + s + "'"),
    st.tuples(
        st.text(alphabet=SAFE_LITERAL_CHARS.replace("'", ""), min_size=0, max_size=6),
        st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=4),
        st.text(alphabet=SAFE_LITERAL_CHARS.replace("'", ""), min_size=0, max_size=6),
    ).map(lambda t: "'" + t[0] + t[1] + t[2] + "'"),
)

non_ascii_ml_basic_string = st.one_of(
    st.just('"""α"""'),
    st.just('"""line α\nline β"""'),
    st.just('"""emoji 😀"""'),
    st.just('"""中\n文"""'),
)

non_ascii_ml_literal_string = st.one_of(
    st.just("'''α'''"),
    st.just("'''line α\nline β'''"),
    st.just("'''emoji 😀 raw'''"),
    st.just("'''中\n文'''"),
)

escaped_basic_string = st.one_of(
    st.just('"\\n"'),
    st.just('"\\t"'),
    st.just('"\\""'),
    st.just('"\\\\"'),
    st.just('"\\u0041"'),
    st.just('"\\u03B1"'),
    st.just('"\\U0001F600"'),
    st.tuples(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=6),
        st.sampled_from(["\\n", "\\t", '\\"', "\\\\", "\\u0041", "\\U0001F600"]),
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=6),
    ).map(lambda t: '"' + t[0] + t[1] + t[2] + '"'),
)

ml_basic_string = st.one_of(
    st.just('""""""'),
    st.just('"""line1\nline2"""'),
    st.just('"""a\\\n  b"""'),
    st.just('"""emoji \\U0001F600"""'),
)

ml_literal_string = st.one_of(
    st.just("''''''"),
    st.just("'''line1\nline2'''"),
    st.just("'''raw \\n text'''"),
)

invalid_basic_string = st.one_of(
    st.just('"\\q"'),
    st.just('"\\u12G4"'),
    st.just('"unterminated'),
)

valid_string = st.one_of(
    safe_basic_inner,
    safe_literal_inner,
    escaped_basic_string,
    ml_basic_string,
    ml_literal_string,
    non_ascii_basic_string,
    non_ascii_literal_string,
    non_ascii_ml_basic_string,
    non_ascii_ml_literal_string,
)

quoted_key = st.one_of(
    safe_basic_inner,
    safe_literal_inner,
    non_ascii_basic_string,
    non_ascii_literal_string,
)
simple_key = st.one_of(unquoted_key, quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda xs: _join(xs, "."))
header_key = st.one_of(simple_key, dotted_key)
regular_key = st.one_of(simple_key, dotted_key)

dec_regular = st.one_of(
    st.just("0"),
    st.just("-0"),
    st.just("1"),
    st.just("-1"),
    st.just("42"),
    st.just("1_000"),
    st.just("9_223_372_036_854_775_807"),
    st.just("-9_223_372_036_854_775_808"),
)

dec_overflow = st.one_of(
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("18446744073709551616"),
)

leading_zero_int = st.one_of(
    st.just("007"),
    st.just("0001"),
    st.just("-00"),
)

hex_int = st.one_of(
    st.just("0x0"),
    st.just("0x1"),
    st.just("0xdead_beef"),
    st.just("0x7fff_ffff_ffff_ffff"),
)

oct_int = st.one_of(
    st.just("0o0"),
    st.just("0o7"),
    st.just("0o755"),
)

bin_int = st.one_of(
    st.just("0b0"),
    st.just("0b1"),
    st.just("0b1010"),
    st.just("0b1111_0000"),
)

integer_value = st.one_of(dec_regular, dec_overflow, leading_zero_int, hex_int, oct_int, bin_int)

float_value = st.one_of(
    st.just("0.0"),
    st.just("-0.0"),
    st.just("1e6"),
    st.just("-2E-3"),
    st.just("3.1415"),
    st.just("1_000.5"),
    st.just("6.02e23"),
    st.just("inf"),
    st.just("-inf"),
    st.just("nan"),
)

local_time_value = st.one_of(
    st.tuples(
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(lambda t: f"{_pad2(t[0])}:{_pad2(t[1])}:{_pad2(t[2])}"),
    st.tuples(
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=1, max_value=999999),
    ).map(lambda t: f"{_pad2(t[0])}:{_pad2(t[1])}:{_pad2(t[2])}.{t[3]}"),
)

date_value = st.one_of(
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
    ).map(lambda t: f"{_pad4(t[0])}-{_pad2(t[1])}-{_pad2(t[2])}"),
    local_time_value,
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(
        lambda t: (
            f"{_pad4(t[0])}-{_pad2(t[1])}-{_pad2(t[2])}"
            f"T{_pad2(t[3])}:{_pad2(t[4])}:{_pad2(t[5])}"
        )
    ),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),
    st.just("1979-05-27 00:32:00.1234567890123456789Z"),
    st.just("07:32:00"),
    st.just("00:32:00.999999"),
)

bool_value = st.sampled_from(["true", "false"])
scalar_value = st.one_of(valid_string, integer_value, float_value, date_value, bool_value)


def _inline_pairs_to_text(pairs, trailing):
    if not pairs:
        return "{}"
    body = ", ".join([f"{k} = {v}" for k, v in pairs])
    if trailing:
        body += ","
    return "{ " + body + " }"


base_value = scalar_value

container_value = st.recursive(
    base_value,
    lambda children: st.one_of(
        st.lists(children, min_size=0, max_size=4).map(lambda xs: "[" + ", ".join(xs) + "]"),
        st.tuples(
            st.lists(
                st.tuples(regular_key, children),
                min_size=0,
                max_size=4,
            ),
            st.booleans(),
        ).map(lambda t: _inline_pairs_to_text(t[0], t[1])),
    ),
    max_leaves=20,
)

deepish_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(
            st.one_of(children, children, children),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[" + xs[0] + "]"),
        st.lists(
            st.tuples(regular_key, st.one_of(children, children, children)),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "{ " + f"{xs[0][0]} = {xs[0][1]}" + " }"),
    ),
    max_leaves=40,
)

depth_biased_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(
            st.one_of(children, children, children, children, children, scalar_value),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[" + xs[0] + "]"),
        st.lists(
            st.tuples(
                regular_key,
                st.one_of(children, children, children, children, children, scalar_value),
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "{ " + xs[0][0] + " = " + xs[0][1] + " }"),
        st.lists(
            st.one_of(children, children, children, children),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[ " + xs[0] + " ]"),
        st.lists(
            st.tuples(
                regular_key,
                st.one_of(children, children, children, children),
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "{ " + xs[0][0] + " = " + xs[0][1] + ", }"),
    ),
    max_leaves=400,
)


@composite
def pair(draw, value_strategy=container_value, allow_duplicate_key=False):
    k = draw(regular_key)
    v = draw(value_strategy)
    comment = draw(st.one_of(st.just(""), st.just(" # c"), st.just(" # α"), st.just(" # 😀")))
    if allow_duplicate_key:
        return k, f"{k} = {v}{comment}"
    return k, f"{k} = {v}{comment}"


@composite
def valid_document(draw, value_strategy=container_value):
    mode = draw(st.integers(min_value=0, max_value=9))
    if mode == 0:
        return ""
    if mode == 1:
        p = draw(pair(value_strategy=value_strategy))
        return p[1]
    if mode == 2:
        ps = draw(st.lists(pair(value_strategy=value_strategy), min_size=1, max_size=4))
        return "\n".join([x[1] for x in ps])
    if mode == 3:
        hdr = draw(header_key)
        ps = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=4))
        lines = [f"[{hdr}]"] + [x[1] for x in ps]
        return "\n".join(lines)
    if mode == 4:
        hdr = draw(header_key)
        ps1 = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=3))
        ps2 = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=3))
        lines = [f"[[{hdr}]]"] + [x[1] for x in ps1] + [f"[[{hdr}]]"] + [x[1] for x in ps2]
        return "\n".join(lines)
    if mode == 5:
        top = draw(st.lists(pair(value_strategy=value_strategy), min_size=1, max_size=3))
        hdr = draw(header_key)
        body = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=3))
        lines = [x[1] for x in top] + [f"[{hdr}]"] + [x[1] for x in body]
        return "\n".join(lines)
    if mode == 6:
        k = draw(regular_key)
        return f"{k} = []"
    if mode == 7:
        k = draw(regular_key)
        return f"{k} = {{}}"
    if mode == 8:
        k = draw(regular_key)
        t = draw(local_time_value)
        return f"{k} = {t}"
    k = draw(quoted_key)
    v = draw(st.one_of(non_ascii_basic_string, non_ascii_literal_string, local_time_value))
    return f"{k} = {v}"


@composite
def duplicate_key_document(draw):
    k = draw(simple_key)
    v1 = draw(scalar_value)
    v2 = draw(container_value)
    return f"{k} = {v1}\n{k} = {v2}"


@composite
def malformed_document(draw):
    mode = draw(st.integers(min_value=0, max_value=7))
    k = draw(regular_key)
    v = draw(container_value)
    if mode == 0:
        return f"{k} {v}"
    if mode == 1:
        return f"{k} = {draw(invalid_basic_string)}"
    if mode == 2:
        return f"{k} = [1, 2"
    if mode == 3:
        return f"{k} = {{ a = 1,\n b = 2 }}"
    if mode == 4:
        return f"[{draw(header_key)}"
    if mode == 5:
        return f"{k} = 'unterminated"
    if mode == 6:
        return f"{k} = {{ a = 1,\n }}"
    return f"{k} = {v}\n[{draw(header_key)}"


@composite
def deep_array_value(draw):
    n = draw(st.integers(min_value=6000, max_value=12000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table_value(draw):
    n = draw(st.integers(min_value=9000, max_value=18000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key_document(draw):
    n = draw(st.integers(min_value=7000, max_value=14000))
    key = "a." * n + "k"
    return f"{key} = 1"


@composite
def deep_mixed_value(draw):
    n = draw(st.integers(min_value=5000, max_value=10000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed_value(draw):
    n = draw(st.integers(min_value=2500, max_value=5000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc(draw, value_text_strategy):
    k = draw(simple_key)
    v = draw(value_text_strategy)
    return f"{k} = {v}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=30000))
    hdr = draw(simple_key)
    lines = [f"[{hdr}]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([valid_document()] * 14),
    *([valid_document(value_strategy=deepish_value)] * 6),
    *([valid_document(value_strategy=depth_biased_value)] * 8),
    *([valid_document(value_strategy=container_value)] * 2),
    duplicate_key_document(),
    malformed_document(),
    deep_doc(deep_array_value()),
    deep_doc(deep_inline_table_value()),
    deep_dotted_key_document(),
    deep_doc(deep_mixed_value()),
    deep_doc(deep_quoted_mixed_value()),
    many_siblings(),
)