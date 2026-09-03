"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-02T22:16:15.001733+00:00
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
dotted_key = st.lists(simple_key, min_size=2, max_size=5).map(lambda xs: _join(xs, "."))
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
    st.just("9_223_372_036_854_775_808"),
)

leading_zero_int = st.one_of(
    st.just("007"),
    st.just("0001"),
    st.just("-00"),
    st.just("01"),
    st.just("0000007"),
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

long_frac_digits = st.integers(min_value=7, max_value=24).map(lambda n: "9" * n)

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
    st.tuples(
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        long_frac_digits,
    ).map(lambda t: f"{_pad2(t[0])}:{_pad2(t[1])}:{_pad2(t[2])}.{t[3]}"),
    st.just("00:32:00.999999"),
    st.just("07:32:00"),
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
    st.tuples(
        st.integers(min_value=1970, max_value=2100),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        long_frac_digits,
        st.sampled_from(["T", "t", " "]),
        st.sampled_from(["Z", "-07:00", "+00:00", "+05:30"]),
    ).map(
        lambda t: (
            f"{_pad4(t[0])}-{_pad2(t[1])}-{_pad2(t[2])}"
            f"{t[7]}{_pad2(t[3])}:{_pad2(t[4])}:{_pad2(t[5])}.{t[6]}{t[8]}"
        )
    ),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),
    st.just("1979-05-27 00:32:00.1234567890123456789Z"),
    st.just("1979-05-27T00:32:00.9999999999999999999Z"),
    st.just("1979-05-27 00:32:00.9999999999999999999-07:00"),
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


def _inline_pairs_to_text_compact(pairs, trailing):
    if not pairs:
        return "{}"
    body = ",".join([f"{k}={v}" for k, v in pairs])
    if trailing:
        body += ","
    return "{" + body + "}"


def _array_text(xs):
    return "[" + ", ".join(xs) + "]"


def _array_text_with_layout(t):
    prefix = t[0]
    xs = t[1]
    suffix = t[2]
    if not xs:
        return "[" + prefix + suffix + "]"
    return "[" + prefix + ", ".join(xs) + suffix + "]"


base_value = scalar_value

container_value = st.recursive(
    base_value,
    lambda children: st.one_of(
        st.lists(children, min_size=0, max_size=5).map(_array_text),
        st.tuples(
            st.sampled_from(["", " ", "\n", "\n# c\n", "\n# α\n", "\n# 😀\n"]),
            st.lists(children, min_size=0, max_size=4),
            st.sampled_from(["", " ", "\n", "\n# tail\n", "\n# α\n"]),
        ).map(_array_text_with_layout),
        st.tuples(
            st.lists(
                st.tuples(regular_key, children),
                min_size=0,
                max_size=5,
            ),
            st.booleans(),
        ).map(lambda t: _inline_pairs_to_text(t[0], t[1])),
    ),
    max_leaves=30,
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
        st.lists(
            st.one_of(children, children),
            min_size=2,
            max_size=3,
        ).map(_array_text),
    ),
    max_leaves=60,
)

depth_biased_value = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        st.lists(
            st.one_of(
                children, children, children, children, children, children, scalar_value
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[" + xs[0] + "]"),
        st.lists(
            st.tuples(
                regular_key,
                st.one_of(
                    children, children, children, children, children, children, scalar_value
                ),
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "{ " + xs[0][0] + " = " + xs[0][1] + " }"),
        st.lists(
            st.one_of(children, children, children, children, children),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[ " + xs[0] + " ]"),
        st.lists(
            st.tuples(
                regular_key,
                st.one_of(children, children, children, children, children),
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "{ " + xs[0][0] + " = " + xs[0][1] + ", }"),
    ),
    max_leaves=1200,
)

rare_scalar_value = st.one_of(
    dec_overflow,
    leading_zero_int,
    st.one_of(
        st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),
        st.just("1979-05-27 00:32:00.1234567890123456789Z"),
        st.just("1979-05-27T00:32:00.9999999999999999999Z"),
        st.just("1979-05-27 00:32:00.9999999999999999999-07:00"),
    ),
    non_ascii_ml_basic_string,
    non_ascii_ml_literal_string,
    escaped_basic_string,
    ml_basic_string,
    ml_literal_string,
    valid_string,
    float_value,
    bool_value,
)

rare_combo_value = st.recursive(
    rare_scalar_value,
    lambda children: st.one_of(
        st.lists(
            st.one_of(
                children, children, children, children, rare_scalar_value
            ),
            min_size=1,
            max_size=1,
        ).map(lambda xs: "[" + xs[0] + "]"),
        st.lists(
            st.one_of(
                children, children, children, rare_scalar_value
            ),
            min_size=2,
            max_size=4,
        ).map(_array_text),
        st.tuples(
            st.lists(
                st.tuples(
                    regular_key,
                    st.one_of(
                        children, children, children, children, rare_scalar_value
                    ),
                ),
                min_size=1,
                max_size=1,
            ),
            st.sampled_from([False, True, True]),
        ).map(lambda t: _inline_pairs_to_text(t[0], t[1])),
        st.tuples(
            st.lists(
                st.tuples(
                    regular_key,
                    st.one_of(
                        children, children, children, rare_scalar_value
                    ),
                ),
                min_size=2,
                max_size=4,
            ),
            st.sampled_from([False, True, True]),
        ).map(lambda t: _inline_pairs_to_text_compact(t[0], t[1])),
    ),
    max_leaves=180,
)


@composite
def chain_value(draw, depth=0, target_min=1200, target_max=5000):
    if depth == 0:
        target = draw(st.integers(min_value=target_min, max_value=target_max))
        return draw(chain_value(depth=1, target_min=target, target_max=target))
    target = target_min
    if depth >= target:
        return draw(scalar_value)
    branch = draw(
        st.one_of(
            st.just("array"),
            st.just("array"),
            st.just("array"),
            st.just("array"),
            st.just("array"),
            st.just("inline"),
            st.just("inline"),
            st.just("inline"),
            st.just("inline"),
            st.just("inline_trailing"),
            st.just("inline_trailing"),
            st.just("inline_trailing"),
        )
    )
    child = draw(chain_value(depth=depth + 1, target_min=target, target_max=target))
    if branch == "array":
        return "[" + child + "]"
    if branch == "inline":
        k = draw(regular_key)
        return "{ " + k + " = " + child + " }"
    k = draw(regular_key)
    return "{ " + k + " = " + child + ", }"


@composite
def pair(draw, value_strategy=container_value, allow_duplicate_key=False):
    k = draw(regular_key)
    v = draw(value_strategy)
    comment = draw(st.one_of(st.just(""), st.just(" # c"), st.just(" # α"), st.just(" # 😀")))
    if allow_duplicate_key:
        return k, f"{k} = {v}{comment}"
    return k, f"{k} = {v}{comment}"


@composite
def pair_with_layout(draw, value_strategy=container_value):
    k = draw(regular_key)
    v = draw(value_strategy)
    ws1 = draw(st.sampled_from([" ", "  ", "\t"]))
    ws2 = draw(st.sampled_from([" ", "  ", "\t"]))
    comment = draw(st.one_of(st.just(""), st.just(" # c"), st.just(" # α"), st.just(" # 😀")))
    return k, f"{k}{ws1}={ws2}{v}{comment}"


@composite
def kv_block(draw, value_strategy=container_value, min_size=1, max_size=4):
    pairs = draw(st.lists(pair_with_layout(value_strategy=value_strategy), min_size=min_size, max_size=max_size))
    return [x[1] for x in pairs]


@composite
def valid_document(draw, value_strategy=container_value):
    mode = draw(st.integers(min_value=0, max_value=15))
    if mode == 0:
        return ""
    if mode == 1:
        p = draw(pair(value_strategy=value_strategy))
        return p[1]
    if mode == 2:
        ps = draw(st.lists(pair(value_strategy=value_strategy), min_size=1, max_size=5))
        return "\n".join([x[1] for x in ps])
    if mode == 3:
        hdr = draw(header_key)
        ps = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=5))
        lines = [f"[{hdr}]"] + [x[1] for x in ps]
        return "\n".join(lines)
    if mode == 4:
        hdr = draw(header_key)
        ps1 = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=4))
        ps2 = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=4))
        lines = [f"[[{hdr}]]"] + [x[1] for x in ps1] + [f"[[{hdr}]]"] + [x[1] for x in ps2]
        return "\n".join(lines)
    if mode == 5:
        top = draw(st.lists(pair(value_strategy=value_strategy), min_size=1, max_size=4))
        hdr = draw(header_key)
        body = draw(st.lists(pair(value_strategy=value_strategy), min_size=0, max_size=4))
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
    if mode == 9:
        k = draw(quoted_key)
        v = draw(st.one_of(non_ascii_basic_string, non_ascii_literal_string, local_time_value))
        return f"{k} = {v}"
    if mode == 10:
        top = draw(kv_block(value_strategy=value_strategy, min_size=1, max_size=3))
        hdr1 = draw(header_key)
        body1 = draw(kv_block(value_strategy=value_strategy, min_size=0, max_size=3))
        hdr2 = draw(header_key)
        body2 = draw(kv_block(value_strategy=value_strategy, min_size=0, max_size=3))
        lines = top + [f"[{hdr1}]"] + body1 + [f"[[{hdr2}]]"] + body2
        return "\n".join(lines)
    if mode == 11:
        hdr = draw(header_key)
        body = draw(kv_block(value_strategy=value_strategy, min_size=1, max_size=5))
        return "# preface\n" + f"[{hdr}]\n" + "\n".join(body)
    if mode == 12:
        hdr = draw(header_key)
        body1 = draw(kv_block(value_strategy=value_strategy, min_size=1, max_size=2))
        body2 = draw(kv_block(value_strategy=value_strategy, min_size=1, max_size=2))
        return "\n".join([f"[[{hdr}]]"] + body1 + [f"[[{hdr}]]"] + body2 + [f"[[{hdr}]]"])
    if mode == 13:
        p1 = draw(pair(value_strategy=value_strategy))
        p2 = draw(pair(value_strategy=value_strategy))
        hdr = draw(header_key)
        p3 = draw(pair(value_strategy=value_strategy))
        return "\n".join([p1[1], "# gap", p2[1], f"[{hdr}]", p3[1]])
    if mode == 14:
        hdr = draw(header_key)
        inner_hdr = draw(header_key)
        top = draw(kv_block(value_strategy=value_strategy, min_size=0, max_size=2))
        body = draw(kv_block(value_strategy=value_strategy, min_size=0, max_size=3))
        return "\n".join(top + [f"[{hdr}]", f"[{inner_hdr}]"] + body)
    p = draw(pair(value_strategy=value_strategy))
    hdr = draw(header_key)
    body = draw(kv_block(value_strategy=value_strategy, min_size=0, max_size=4))
    return "\n".join([p[1], f"[[{hdr}]]"] + body)


@composite
def rare_combo_document(draw):
    mode = draw(st.integers(min_value=0, max_value=7))
    hdr1 = draw(header_key)
    hdr2 = draw(header_key)
    hdr3 = draw(header_key)
    k1 = draw(regular_key)
    k2 = draw(regular_key)
    k3 = draw(regular_key)
    k4 = draw(regular_key)
    v1 = draw(rare_combo_value)
    v2 = draw(rare_combo_value)
    v3 = draw(rare_combo_value)
    v4 = draw(rare_combo_value)
    if mode == 0:
        return "\n".join([
            f"[[{hdr1}]]",
            f"{k1} = {v1}",
            f"{k2} = {v2}",
        ])
    if mode == 1:
        return "\n".join([
            f"[{hdr1}]",
            f"[[{hdr2}]]",
            f"{k1} = {v1}",
            f"{k2} = {v2}",
        ])
    if mode == 2:
        return "\n".join([
            f"[[{hdr1}]]",
            f"{k1} = {v1}",
            f"[[{hdr1}]]",
            f"{k2} = {v2}",
            f"{k3} = {v3}",
        ])
    if mode == 3:
        return "\n".join([
            f"{k1} = {v1}",
            f"[[{hdr1}]]",
            f"{k2} = {v2}",
            f"[{hdr2}]",
            f"{k3} = {v3}",
        ])
    if mode == 4:
        return "\n".join([
            f"[{hdr1}]",
            f"{k1} = {v1}",
            f"[[{hdr2}]]",
            f"{k2} = {v2}",
            f"[[{hdr2}]]",
            f"{k3} = {v3}",
        ])
    if mode == 5:
        return "\n".join([
            f"[[{hdr1}]]",
            f"{k1} = {v1}",
            f"[{hdr2}]",
            f"{k2} = {v2}",
            f"[[{hdr3}]]",
            f"{k3} = {v3}",
        ])
    if mode == 6:
        return "\n".join([
            f"[[{hdr1}]]",
            f"{k1} = [ {v1} ]",
            f"{k2} = {{ {draw(regular_key)} = {v2}, }}",
            f"{k3} = {v3}",
        ])
    return "\n".join([
        f"{k1} = {v1}",
        f"[{hdr1}]",
        f"{k2} = {v2}",
        f"[[{hdr2}]]",
        f"{k3} = {v3}",
        f"{k4} = {v4}",
    ])


@composite
def depth_hunter_document(draw):
    mode = draw(st.integers(min_value=0, max_value=5))
    k = draw(simple_key)
    if mode == 0:
        v = draw(chain_value(target_min=1800, target_max=7000))
        return f"{k} = {v}"
    if mode == 1:
        v = draw(chain_value(target_min=4000, target_max=12000))
        return f"{k} = {v}"
    if mode == 2:
        p1 = draw(pair(value_strategy=container_value))
        v = draw(chain_value(target_min=2500, target_max=9000))
        return "\n".join([p1[1], f"{k} = {v}"])
    if mode == 3:
        hdr = draw(header_key)
        v = draw(chain_value(target_min=3000, target_max=10000))
        return "\n".join([f"[{hdr}]", f"{k} = {v}"])
    if mode == 4:
        hdr = draw(header_key)
        p1 = draw(pair(value_strategy=container_value))
        v = draw(chain_value(target_min=5000, target_max=15000))
        return "\n".join([p1[1], f"[[{hdr}]]", f"{k} = {v}"])
    v = draw(chain_value(target_min=8000, target_max=30000))
    return f"{k} = {v}"


@composite
def duplicate_key_document(draw):
    k = draw(simple_key)
    v1 = draw(scalar_value)
    v2 = draw(container_value)
    return f"{k} = {v1}\n{k} = {v2}"


@composite
def malformed_document(draw):
    mode = draw(st.integers(min_value=0, max_value=9))
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
    if mode == 7:
        return f"{k} = {v}\n[{draw(header_key)}"
    if mode == 8:
        return f"{k} = [1,,2]"
    return f"{k} = {{ a = 1 b = 2 }}"


@composite
def deep_array_value(draw):
    n = draw(st.integers(min_value=60000, max_value=120000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table_value(draw):
    n = draw(st.integers(min_value=85000, max_value=115000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key_document(draw):
    n = draw(st.integers(min_value=100000, max_value=130000))
    key = "a." * n + "k"
    return f"{key} = 1"


@composite
def deep_mixed_value(draw):
    n = draw(st.integers(min_value=60000, max_value=80000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed_value(draw):
    n = draw(st.integers(min_value=20000, max_value=45000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc(draw, value_text_strategy):
    k = draw(simple_key)
    v = draw(value_text_strategy)
    return f"{k} = {v}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10000, max_value=60000))
    hdr = draw(simple_key)
    lines = [f"[{hdr}]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([valid_document()] * 12),
    *([valid_document(value_strategy=container_value)] * 6),
    *([valid_document(value_strategy=deepish_value)] * 8),
    *([valid_document(value_strategy=depth_biased_value)] * 10),
    *([valid_document(value_strategy=rare_combo_value)] * 10),
    *([rare_combo_document()] * 10),
    *([depth_hunter_document()] * 6),
    duplicate_key_document(),
    malformed_document(),
    deep_doc(deep_array_value()),
    deep_doc(deep_inline_table_value()),
    deep_dotted_key_document(),
    deep_doc(deep_mixed_value()),
    deep_doc(deep_quoted_mixed_value()),
    many_siblings(),
)