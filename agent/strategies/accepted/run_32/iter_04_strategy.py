"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-22T08:15:50.223426+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
SAFE_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()~`+='<>|{}"
NON_ASCII_CHARS = "áéíóúñçαβγδ中文ðÞæøå🚀"

valid_escape = st.one_of(
    st.sampled_from(["\\\\", '\\"', "\\b", "\\f", "\\n", "\\r", "\\t"]),
    st.integers(0x0020, 0xD7FF).map(lambda x: f"\\u{x:04x}"),
    st.integers(0x0020, 0xD7FF).map(lambda x: f"\\u{x:04X}"),
    st.integers(0xE000, 0xFFFF).map(lambda x: f"\\u{x:04x}"),
    st.integers(0xE000, 0xFFFF).map(lambda x: f"\\u{x:04X}"),
    st.integers(0x00010000, 0x0010FFFF).map(lambda x: f"\\U{x:08x}"),
    st.integers(0x00010000, 0x0010FFFF).map(lambda x: f"\\U{x:08X}"),
)

safe_text = st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=10)
non_ascii_text = st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=5)

basic_string = st.lists(
    st.one_of(safe_text, non_ascii_text, valid_escape),
    min_size=0,
    max_size=4,
).map(lambda parts: f'"{"".join(parts)}"')

literal_string = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=10),
        non_ascii_text,
    ),
    min_size=0,
    max_size=4,
).map(lambda parts: f"'{"".join(parts)}'")

ml_basic_string = st.lists(
    st.one_of(
        safe_text,
        non_ascii_text,
        valid_escape,
        st.just("\n"),
        st.just("\\\n"),
    ),
    min_size=0,
    max_size=4,
).map(lambda parts: '"""' + "".join(parts).replace('"""', '""') + '"""')

ml_literal_string = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=10),
        non_ascii_text,
        st.just("\n"),
    ),
    min_size=0,
    max_size=4,
).map(lambda parts: "'''" + "".join(parts).replace("'''", "''") + "'''")

string_val = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
)

extreme_vals = st.one_of(
    st.sampled_from([
        "9223372036854775808",  # INT64_MAX + 1
        "-9223372036854775809",  # INT64_MIN - 1
        "18446744073709551615",  # UINT64_MAX
        "007",  # Leading zero int
        "0123",
        "-042",
        "inf",
        "-inf",
        "+inf",
        "nan",
        "-nan",
        "+nan",
        "1.0e+999",
        "-1.0e+999",
        "0x1a2b",
        "0o755",
        "0b10101",
        "0xDEADBEEF",
        "0o777",
        "0b11111111",
        "1_000_000",
        "1979-05-27T00:32:00.9999999999999999999-07:00",  # Over-long frac seconds
        "2021-05-01T12:00:00.123456789Z",
        "2021-05-01T12:00:00Z",
        "2021-05-01 12:00:00.500+02:00",
        "2021-05-01",
        "12:00:00",
        "12:00:00.000000001",
    ]),
    st.integers(10, 30).map(lambda n: f"2023-01-01T00:00:00.{'9' * n}Z"),
    st.integers(min_value=9223372036854775807, max_value=9223372036854775820).map(
        str
    ),
    st.integers(
        min_value=-9223372036854775830, max_value=-9223372036854775808
    ).map(str),
)

scalar_val = st.one_of(
    st.integers(-10000, 10000).map(str),
    st.floats(allow_nan=False, allow_infinity=False).map(str),
    st.sampled_from(["true", "false"]),
    string_val,
    extreme_vals,
)


@composite
def safe_key(draw):
    ktype = draw(st.integers(0, 2))
    raw = draw(st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=6))
    if ktype == 0:
        return raw
    elif ktype == 1:
        return f'"{raw}"'
    else:
        raw2 = draw(st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=6))
        return f"{raw}.{raw2}"


@composite
def array_val(draw, depth=0):
    if depth >= 3:
        elem_strat = st.one_of(scalar_val, extreme_vals)
    else:
        elem_strat = st.one_of(
            scalar_val,
            extreme_vals,
            array_val(depth=depth + 1),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    elements = draw(st.lists(elem_strat, min_size=0, max_size=4))
    trailing = draw(st.sampled_from(["", ","])) if elements else ""
    return f"[{', '.join(elements)}{trailing}]"


@composite
def inline_table_val(draw, depth=0):
    if depth >= 3:
        val_strat = st.one_of(scalar_val, extreme_vals)
    else:
        val_strat = st.one_of(
            scalar_val,
            extreme_vals,
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    n = draw(st.integers(0, 4))
    pairs = []
    for _ in range(n):
        k = draw(safe_key())
        v = draw(val_strat)
        pairs.append(f"{k} = {v}")
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def toml_value(draw):
    return draw(
        st.one_of(
            scalar_val,
            array_val(),
            inline_table_val(),
            extreme_vals,
        )
    )


@composite
def document(draw):
    num_sections = draw(st.integers(0, 4))
    lines = []

    num_top_kv = draw(st.integers(0, 4))
    for _ in range(num_top_kv):
        k = draw(safe_key())
        v = draw(toml_value())
        comment = draw(st.sampled_from(["", " # comment", ""]))
        lines.append(f"{k} = {v}{comment}")

    for _ in range(num_sections):
        sec_type = draw(st.integers(0, 2))
        tbl_name = draw(safe_key())
        if sec_type == 0:
            lines.append(f"[{tbl_name}]")
        else:
            lines.append(f"[[{tbl_name}]]")

        num_kv = draw(st.integers(1, 4))
        for _ in range(num_kv):
            k = draw(safe_key())
            if sec_type >= 1:
                v = draw(
                    st.one_of(
                        inline_table_val(depth=0),
                        inline_table_val(depth=1),
                        array_val(depth=0),
                        extreme_vals,
                        toml_value(),
                    )
                )
            else:
                v = draw(toml_value())
            comment = draw(st.sampled_from(["", " # comment", ""]))
            lines.append(f"{k} = {v}{comment}")

    return "\n".join(lines)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return "a." * n + "k"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_doc_val(draw, strat):
    val = draw(strat)
    return f"deep_key = {val}"


@composite
def deep_doc_key(draw, strat):
    key_str = draw(strat)
    return f"{key_str} = 1"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 25),
    deep_doc_val(deep_array()),
    deep_doc_val(deep_inline_table()),
    deep_doc_key(deep_dotted_key()),
    deep_doc_val(deep_mixed_nesting()),
    deep_doc_val(deep_quoted_mixed()),
    many_siblings(),
)