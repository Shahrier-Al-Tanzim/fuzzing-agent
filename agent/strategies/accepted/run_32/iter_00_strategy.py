"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-08-22T07:44:42.379489+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =+:;.,<>/?!@#$%^&*()~`"

scalar_val = st.one_of(
    st.integers(-10000, 10000).map(str),
    st.floats(allow_nan=False, allow_infinity=False).map(str),
    st.sampled_from(["true", "false"]),
    st.text(alphabet=SAFE_STR_CHARS, min_size=0, max_size=10).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SAFE_STR_CHARS, min_size=0, max_size=10).map(
        lambda s: f"'{s}'"
    ),
    st.sampled_from([
        "9223372036854775808",
        "-9223372036854775809",
        "007",
        "inf",
        "-inf",
        "nan",
        "0x1a2b",
        "0o755",
        "0b10101",
        "1_000_000",
        "1979-05-27T00:32:00.9999999999999999999-07:00",
        "2021-05-01T12:00:00Z",
        "2021-05-01",
        "12:00:00",
    ]),
)


@composite
def array_val(draw, depth=0):
    if depth >= 3:
        elem_strat = scalar_val
    else:
        elem_strat = st.one_of(
            scalar_val,
            array_val(depth=depth + 1),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    elements = draw(st.lists(elem_strat, min_size=0, max_size=4))
    trailing = draw(st.sampled_from(["", ","])) if elements else ""
    return f"[{', '.join(elements)}{trailing}]"


@composite
def inline_table_val(draw, depth=0):
    if depth >= 3:
        val_strat = scalar_val
    else:
        val_strat = st.one_of(
            scalar_val,
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    n = draw(st.integers(0, 3))
    pairs = []
    for i in range(n):
        k = f"ik{i}"
        v = draw(val_strat)
        pairs.append(f"{k} = {v}")
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def toml_value(draw):
    return draw(st.one_of(scalar_val, array_val(), inline_table_val()))


@composite
def unique_key(draw, idx, prefix="k"):
    ktype = draw(st.integers(0, 2))
    raw = draw(st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=6))
    if ktype == 0:
        return f"{prefix}_{idx}_{raw}"
    elif ktype == 1:
        return f'"{prefix}_{idx}_{raw}"'
    else:
        raw2 = draw(st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=6))
        return f"{prefix}_{idx}.{raw2}"


@composite
def document(draw):
    num_sections = draw(st.integers(0, 4))
    lines = []

    num_top_kv = draw(st.integers(0, 4))
    for i in range(num_top_kv):
        k = draw(unique_key(i, prefix="top"))
        v = draw(toml_value())
        comment = draw(st.sampled_from(["", " # comment", ""]))
        lines.append(f"{k} = {v}{comment}")

    for sec_idx in range(num_sections):
        sec_type = draw(st.integers(0, 1))
        tbl_name = f"sec_{sec_idx}"
        if sec_type == 0:
            lines.append(f"[{tbl_name}]")
        else:
            lines.append(f"[[{tbl_name}]]")

        num_kv = draw(st.integers(1, 4))
        for i in range(num_kv):
            k = draw(unique_key(i, prefix="sub_k"))
            v = draw(toml_value())
            lines.append(f"{k} = {v}")

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