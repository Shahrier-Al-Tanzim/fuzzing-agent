"""Generated strategy - iteration 1, attempt 1.
accepted: False
generated: 2026-08-20T06:22:06.732900+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]=+|éèàçùαβγñ漢字🎉€"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]=+|\\\"éèàçùαβγñ漢字🎉€"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=15)
quoted_basic_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=15).map(lambda s: f'"{s}"')
quoted_literal_key = st.text(alphabet=LITERAL_STR_CHARS, min_size=1, max_size=15).map(lambda s: f"'{s}'")
simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key, dotted_key)

quoted_basic = st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"')
quoted_literal = st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'")
ml_basic = st.text(alphabet=BASIC_STR_CHARS + "\n\t", min_size=0, max_size=20).map(lambda s: f'"""{s.replace("ascii", "test")}"""')
ml_literal = st.text(alphabet=BASIC_STR_CHARS + "\n\t", min_size=0, max_size=20).map(lambda s: "'''" + s.replace("'''", "' '") + "'''")

comment_strat = st.one_of(
    st.just(""),
    st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda c: f" # {c}")
)

scalar_value = st.one_of(
    # integers & int_underscore & overflow & leading zero
    st.integers(min_value=-9223372036854775808, max_value=9223372036854775807).map(str),
    st.sampled_from([
        "9223372036854775808", "-9223372036854775809", "007", "0123",
        "1_000", "+1_000_000", "-9_223_372_036_854_775_808", "1_0_0_0"
    ]),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 65535).map(lambda x: f"0o{x:o}"),
    st.integers(0, 65535).map(lambda x: f"0b{x:b}"),
    st.sampled_from(["0x12_34", "0o7_5_5", "0b1_0_1_0_1"]),
    # floats
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["inf", "-inf", "+inf", "nan", "+nan", "1e10", "1.0e-5"]),
    # booleans
    st.sampled_from(["true", "false"]),
    # strings & multiline strings & non_ascii
    quoted_basic,
    quoted_literal,
    ml_basic,
    ml_literal,
    # unicode_escape
    st.integers(0, 0xFFFF).map(lambda x: f'"val_\\u{x:04x}_end"'),
    st.integers(0, 0x10FFFF).map(lambda x: f'"val_\\U{x:08x}_end"'),
    st.sampled_from(['"hello\\nworld"', '"val\\twith\\tescapes"', '"bad\\zescape"']),
    # date_time & LOCAL_TIME
    st.tuples(
        st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.just("1979-05-27T00:32:00.9999999999999999999Z"),
    st.tuples(st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59), st.integers(0, 999999)).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]:06d}")
)

@composite
def recursive_value(draw, depth=0):
    if depth >= 220:
        return draw(scalar_value)

    is_leaf = draw(st.booleans()) if depth < 3 else (draw(st.integers(1, 10)) == 1)
    if is_leaf and depth > 0:
        return draw(scalar_value)

    container_type = draw(st.sampled_from(["array", "inline_table"]))
    if container_type == "array":
        size = draw(st.integers(0, 3)) if depth < 3 else 1
        elems = [draw(recursive_value(depth=depth + 1)) for _ in range(size)]
        body = ", ".join(elems)
        if draw(st.booleans()) and elems:
            body += ","
        return f"[{body}]"
    else:
        size = draw(st.integers(0, 3)) if depth < 3 else 1
        pairs = []
        for i in range(size):
            v = draw(recursive_value(depth=depth + 1))
            pairs.append(f"k{i} = {v}")
        body = ", ".join(pairs)
        if draw(st.booleans()) and pairs:
            body += ","
        return f"{{{body}}}"

value_strategy = recursive_value()

@composite
def document(draw):
    lines = []
    num_items = draw(st.integers(1, 8))
    tbl_idx = 0
    kv_idx = 0
    for _ in range(num_items):
        kind = draw(st.sampled_from(["kv", "table", "array_table"]))
        comment = draw(comment_strat)
        if kind == "kv":
            kv_idx += 1
            k_base = draw(simple_key)
            k = f"k_{kv_idx}_{k_base}" if k_base.startswith('"') or k_base.startswith("'") else f"{k_base}_{kv_idx}"
            v = draw(value_strategy)
            lines.append(f"{k} = {v}{comment}")
        elif kind == "table":
            tbl_idx += 1
            lines.append(f"[tbl_{tbl_idx}]{comment}")
        else:
            tbl_idx += 1
            lines.append(f"[[arr_tbl_{tbl_idx}]]{comment}")
    return "\n".join(lines)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return f"v = {'[' * n}1{']' * n}"

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return f"v = {'{a=' * n}1{'}' * n}"

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return f"{'a.' * n}k = 1"

@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return f"v = {'[{a=' * n}1{'}]' * n}"

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    many_siblings()
)