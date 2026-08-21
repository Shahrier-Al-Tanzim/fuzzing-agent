"""Generated strategy - iteration 1, attempt 1.
accepted: False
generated: 2026-08-21T09:23:11.694068+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&()*+,-./:;<=>?@[]^_`{|}~ "
NON_ASCII = "Éñüαβγδこんにちは世界"

unquoted_key_strat = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_key_strat = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII, min_size=1, max_size=10).map(lambda s: f'"{s}"')
simple_key_strat = st.one_of(unquoted_key_strat, quoted_key_strat)

@composite
def dotted_key_strat(draw):
    parts = draw(st.lists(simple_key_strat, min_size=2, max_size=4))
    return ".".join(parts)

def key_strat():
    return st.one_of(simple_key_strat, dotted_key_strat())

bool_strat = st.sampled_from(["true", "false"])

bin_int_strat = st.text(alphabet="01", min_size=1, max_size=16).map(lambda b: f"0b{b}")
hex_int_strat = st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=8).map(lambda h: f"0x{h}")
oct_int_strat = st.text(alphabet="01234567", min_size=1, max_size=8).map(lambda o: f"0o{o}")
dec_int_strat = st.one_of(
    st.integers().map(str),
    st.sampled_from([
        "0", "-0", "9223372036854775807", "-9223372036854775808",
        "9223372036854775808", "-9223372036854775809", "18446744073709551615",
        "00", "07", "007", "0123", "-05"
    ])
)
int_strat = st.one_of(dec_int_strat, hex_int_strat, oct_int_strat, bin_int_strat)

float_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "0.0", "-0.0", "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "1.0e+99", "1e-5", "3.14159_26535", "1_0.0_1"
    ])
)

string_strat = st.one_of(
    st.text(alphabet=BASIC_STR_CHARS + NON_ASCII, min_size=0, max_size=12).map(lambda s: f'"{s}"'),
    st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII, min_size=0, max_size=12).map(lambda s: f"'{s}'"),
    st.text(alphabet=BASIC_STR_CHARS + NON_ASCII + "\n ", min_size=0, max_size=20).map(lambda s: f'"""{s}"""'),
    st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII + "\n ", min_size=0, max_size=20).map(lambda s: f"'''{s}'''"),
    st.sampled_from([
        '"hello\\nworld"', '"escaped \\" quote"', '"unicode \\u0041 \\U0001F600"',
        '"bad escape \\z"', '"invalid unicode \\uGGGG"',
        '"日本語テスト"', "'café'", '"\u00e9"'
    ])
)

@composite
def datetime_strat(draw):
    y = draw(st.integers(1970, 2099))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    frac = draw(st.sampled_from(["", ".123", ".9999999999999999999", ".000000001"]))
    offset = draw(st.sampled_from(["Z", "+00:00", "-08:00", "+05:30"]))
    delim = draw(st.sampled_from(["T", "t", " "]))

    kind = draw(st.sampled_from(["local_date", "local_time", "offset_dt", "local_dt"]))
    if kind == "local_date":
        return f"{y:04d}-{m:02d}-{d:02d}"
    elif kind == "local_time":
        return f"{h:02d}:{mi:02d}:{s:02d}{frac}"
    elif kind == "local_dt":
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac}"
    else:
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac}{offset}"

scalar_value = st.one_of(bool_strat, int_strat, float_strat, string_strat, datetime_strat())

@composite
def shallow_toml_value(draw, depth=0):
    if depth >= 5:
        return draw(scalar_value)

    kind = draw(st.sampled_from(["scalar", "array", "inline"]))
    if kind == "scalar":
        return draw(scalar_value)
    elif kind == "array":
        num_elems = draw(st.integers(0, 4))
        elems = [draw(shallow_toml_value(depth=depth + 1)) for _ in range(num_elems)]
        comma = draw(st.sampled_from([", ", ",", ", \n", ""])) if elems else ""
        return f"[{', '.join(elems)}{comma}]"
    else:
        num_pairs = draw(st.integers(0, 4))
        pairs = []
        for i in range(num_pairs):
            k = f"k{i}_" + draw(unquoted_key_strat)
            v = draw(shallow_toml_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        trailing_comma = draw(st.sampled_from([", ", "", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing_comma}}}"

@composite
def deep_toml_value(draw, depth=0, max_depth=200):
    if depth >= max_depth:
        return draw(scalar_value)

    choice = draw(st.sampled_from(["array", "array", "array", "inline", "scalar"]))
    if choice == "array":
        val = draw(deep_toml_value(depth=depth + 1, max_depth=max_depth))
        return f"[{val}]"
    elif choice == "inline":
        k = f"dk{depth}"
        val = draw(deep_toml_value(depth=depth + 1, max_depth=max_depth))
        trailing = draw(st.sampled_from(["", ","]))
        return f"{{{k} = {val}{trailing}}}"
    else:
        return draw(scalar_value)

comment_strat = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII, min_size=0, max_size=15).map(lambda s: f"# {s}")

@composite
def key_value_pair(draw, key_prefix="key", deep=False, max_depth=200):
    base_k = draw(key_strat())
    k = f"{key_prefix}_{base_k}"
    if deep:
        v = draw(deep_toml_value(max_depth=max_depth))
    else:
        v = draw(shallow_toml_value())
    eq = draw(st.sampled_from([" = ", "=", "  =  "]))
    return f"{k}{eq}{v}"

@composite
def table_header(draw, table_prefix="table"):
    base_k = draw(key_strat())
    k = f"{table_prefix}_{base_k}"
    is_array_table = draw(st.booleans())
    if is_array_table:
        return f"[[{k}]]"
    else:
        return f"[{k}]"

malformed_line_strat = st.sampled_from([
    "key = ",
    "= value",
    "key value",
    "[unclosed_table",
    "[[unclosed_array_table",
    "{ unclosed = inline",
    "\"unclosed_string = 123",
    "key = { a = 1, b = 2, }"
])

@composite
def document_builder(draw, deep_bias=False):
    num_lines = draw(st.integers(1, 15))
    lines = []
    max_d = draw(st.integers(50, 250)) if deep_bias else 5

    for idx in range(num_lines):
        line_type = draw(st.sampled_from([
            "pair", "pair", "pair", "table", "comment", "blank", "malformed"
        ]))

        if line_type == "pair":
            lines.append(draw(key_value_pair(key_prefix=f"k{idx}", deep=deep_bias, max_depth=max_d)))
        elif line_type == "table":
            lines.append(draw(table_header(table_prefix=f"t{idx}")))
        elif line_type == "comment":
            lines.append(draw(comment_strat))
        elif line_type == "blank":
            lines.append("")
        elif line_type == "malformed":
            lines.append(draw(malformed_line_strat))

    return "\n".join(lines)

toml_strategy = st.one_of(
    document_builder(deep_bias=False),
    document_builder(deep_bias=True),
    st.just("")
)