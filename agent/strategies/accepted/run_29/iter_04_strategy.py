"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-21T09:34:00.739123+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

ALPHA_NUM_DASH_UNDERSCORE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !\"#$%&()*+,-./:;<=>?@[]^_`{|}~"
NON_ASCII_CHARS = "éàèùâêîôûäëïöüÿçñßαβγδε中华âñµÆØÅäöü"

unquoted_key_strat = st.text(alphabet=ALPHA_NUM_DASH_UNDERSCORE, min_size=1, max_size=10)

@composite
def safe_key(draw, prefix=""):
    kind = draw(st.sampled_from(["unquoted", "quoted_basic", "quoted_literal", "dotted"]))
    if kind == "unquoted":
        base = draw(unquoted_key_strat)
        return f"{prefix}{base}" if prefix else base
    elif kind == "quoted_basic":
        base = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10))
        return f'"{prefix}{base}"'
    elif kind == "quoted_literal":
        base = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10))
        return f"'{prefix}{base}'"
    else:
        p1 = draw(unquoted_key_strat)
        p2 = draw(unquoted_key_strat)
        return f"{prefix}{p1}.{p2}" if prefix else f"{p1}.{p2}"

bool_strat = st.sampled_from(["true", "false"])

bin_int_strat = st.one_of(
    st.integers(min_value=0, max_value=65535).map(lambda x: f"0b{bin(x)[2:]}"),
    st.sampled_from(["0b0", "0b1", "0b1101_0010", "0b0_1", "0b101010"])
)

hex_int_strat = st.one_of(
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.sampled_from(["0x0", "0xDEADBEEF", "0x1234_5678", "0xfe", "0x7fffffffffffffff", "0x8000000000000000"])
)

oct_int_strat = st.one_of(
    st.integers(min_value=0, max_value=0o7777).map(lambda x: f"0o{oct(x)[2:]}"),
    st.sampled_from(["0o0", "0o755", "0o0_7", "0o644", "0o1777777777777777777777"])
)

dec_int_strat = st.one_of(
    st.integers().map(str),
    st.sampled_from([
        "0", "-0", "9223372036854775807", "-9223372036854775808",
        "9223372036854775808", "-9223372036854775809", "18446744073709551615",
        "00", "07", "007", "0123", "-05", "1_000_000"
    ])
)

int_strat = st.one_of(dec_int_strat, hex_int_strat, oct_int_strat, bin_int_strat)

float_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "0.0", "-0.0", "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "1.0e+99", "1e-5", "3.14159_26535", "1_0.0_1", "9223372036854775808.0"
    ])
)

basic_str = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS, min_size=0, max_size=12).map(lambda s: f'"{s}"')
literal_str = st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII_CHARS, min_size=0, max_size=12).map(lambda s: f"'{s}'")
ml_basic_str = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS + " ", min_size=0, max_size=20).map(lambda s: f'"""{s}"""')
ml_literal_str = st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII_CHARS + " ", min_size=0, max_size=20).map(lambda s: f"'''{s}'''")

escaped_str = st.sampled_from([
    '"hello\\nworld"',
    '"escaped \\" quote"',
    '"unicode \\u0041 \\U0001F600"',
    '"non_ascii_\\u00E9_test"',
    '"bad escape \\z"',
    '"invalid unicode \\uGGGG"'
])

string_strat = st.one_of(basic_str, literal_str, ml_basic_str, ml_literal_str, escaped_str)

@composite
def datetime_strat(draw):
    y = draw(st.integers(1970, 2099))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    frac = draw(st.sampled_from(["", ".123", ".9999999999999999999", ".000000001", ".5", ".123456789123456"]))
    offset = draw(st.sampled_from(["Z", "+00:00", "-08:00", "+05:30"]))
    delim = draw(st.sampled_from(["T", "t", " "]))

    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    time_str = f"{h:02d}:{mi:02d}:{s:02d}{frac}"

    kind = draw(st.sampled_from(["offset_dt", "local_dt", "local_date", "local_time"]))
    if kind == "offset_dt":
        return f"{date_str}{delim}{time_str}{offset}"
    elif kind == "local_dt":
        return f"{date_str}{delim}{time_str}"
    elif kind == "local_date":
        return date_str
    else:
        return time_str

@composite
def extreme_value(draw):
    kind = draw(st.sampled_from(["int_overflow", "leading_zero_int", "long_frac_dt", "extreme_float", "escaped_str"]))
    if kind == "int_overflow":
        return draw(st.sampled_from([
            "9223372036854775808", "-9223372036854775809",
            "18446744073709551615", "999999999999999999999999999999"
        ]))
    elif kind == "leading_zero_int":
        return draw(st.sampled_from(["007", "00", "07", "0123", "-05", "00001"]))
    elif kind == "long_frac_dt":
        frac = draw(st.sampled_from([
            ".9999999999999999999", ".0000000000000000001",
            ".123456789123456789", ".999999"
        ]))
        return f"1979-05-27T00:32:00{frac}Z"
    elif kind == "extreme_float":
        return draw(st.sampled_from([
            "1e9999", "-1e9999", "1.0e-9999", "0.0", "-0.0", "nan", "-nan", "inf", "-inf"
        ]))
    else:
        return draw(st.sampled_from([
            '"\\u0000"', '"\\t\\n\\r\\\\"', '"\\U0001F600"', '"escaped \\" quote"'
        ]))

scalar_value = st.one_of(
    bool_strat, int_strat, float_strat, string_strat, datetime_strat(), extreme_value()
)

@composite
def toml_value(draw, depth=0):
    if depth >= 5:
        return draw(st.one_of(scalar_value, extreme_value()))
    
    kind = draw(st.sampled_from(["scalar", "array", "inline"]))
    if kind == "scalar":
        return draw(st.one_of(scalar_value, extreme_value()))
    elif kind == "array":
        num_elems = draw(st.integers(0, 3))
        elems = [draw(toml_value(depth=depth + 1)) for _ in range(num_elems)]
        comma = draw(st.sampled_from([", ", "", ","])) if elems else ""
        return f"[{', '.join(elems)}{comma}]"
    else:
        num_pairs = draw(st.integers(0, 3))
        pairs = []
        for i in range(num_pairs):
            suffix = draw(unquoted_key_strat)
            k = f"ik{i}_" + suffix
            v = draw(toml_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        trailing_comma = draw(st.sampled_from([", ", "", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing_comma}}}"

@composite
def deep_toml_value(draw, min_depth=20, max_depth=500):
    depth = draw(st.integers(min_depth, max_depth))
    val = draw(st.one_of(scalar_value, extreme_value()))
    kind = draw(st.sampled_from(["array", "inline", "trailing_comma_inline", "mixed_inline_array"]))
    if kind == "array":
        return "[" * depth + val + "]" * depth
    elif kind == "inline":
        prefix = "".join(f"k{i} = {{" for i in range(depth))
        suffix = "}" * depth
        return prefix + val + suffix
    elif kind == "trailing_comma_inline":
        prefix = "".join(f"k{i} = {{" for i in range(depth))
        suffix = "}" * depth
        return prefix + val + ", " + suffix
    else:
        chunks_left = []
        chunks_right = []
        for i in range(depth):
            if i % 2 == 0:
                chunks_left.append("[")
                chunks_right.append("]")
            else:
                chunks_left.append(f"k{i} = {{")
                chunks_right.append("}")
        return "".join(chunks_left) + val + "".join(reversed(chunks_right))

comment_strat = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS, min_size=0, max_size=15).map(lambda s: f"# {s}")

@composite
def document_builder(draw, deep_mode="none"):
    num_items = draw(st.integers(1, 10))
    lines = []
    
    for idx in range(num_items):
        item_type = draw(st.sampled_from([
            "pair", "pair", "table", "array_table", "array_table_deep", "comment", "blank"
        ]))
        
        if item_type == "pair":
            prefix = f"k{idx}_"
            k = draw(safe_key(prefix=prefix))
            if deep_mode == "ultra_deep":
                v = draw(deep_toml_value(min_depth=10000, max_depth=95000))
            elif deep_mode == "extreme":
                v = draw(deep_toml_value(min_depth=500, max_depth=5000))
            elif deep_mode == "moderate":
                v = draw(deep_toml_value(min_depth=10, max_depth=200))
            else:
                v = draw(toml_value())
            eq = draw(st.sampled_from([" = ", "=", "  =  "]))
            lines.append(f"{k}{eq}{v}")
            
        elif item_type == "table":
            prefix = f"t{idx}_"
            k = draw(safe_key(prefix=prefix))
            lines.append(f"[{k}]")
            num_inner = draw(st.integers(1, 3))
            for j in range(num_inner):
                ik = draw(safe_key(prefix=f"tk{j}_"))
                if deep_mode == "ultra_deep":
                    iv = draw(deep_toml_value(min_depth=10000, max_depth=95000))
                elif deep_mode == "extreme":
                    iv = draw(deep_toml_value(min_depth=500, max_depth=5000))
                else:
                    iv = draw(toml_value())
                lines.append(f"{ik} = {iv}")

        elif item_type == "array_table":
            prefix = f"at{idx}_"
            k = draw(safe_key(prefix=prefix))
            lines.append(f"[[{k}]]")
            num_inner = draw(st.integers(1, 3))
            for j in range(num_inner):
                ik = draw(safe_key(prefix=f"atk{j}_"))
                iv = draw(toml_value())
                lines.append(f"{ik} = {iv}")

        elif item_type == "array_table_deep":
            prefix = f"atd{idx}_"
            k = draw(safe_key(prefix=prefix))
            lines.append(f"[[{k}]]")
            ik = draw(safe_key(prefix="deep_k_"))
            if deep_mode == "ultra_deep":
                iv = draw(deep_toml_value(min_depth=10000, max_depth=95000))
            elif deep_mode == "extreme":
                iv = draw(deep_toml_value(min_depth=500, max_depth=5000))
            else:
                iv = draw(deep_toml_value(min_depth=5, max_depth=80))
            lines.append(f"{ik} = {iv}")

        elif item_type == "comment":
            lines.append(draw(comment_strat))
            
        elif item_type == "blank":
            lines.append("")
            
    return "\n".join(lines)

toml_strategy = st.one_of(
    document_builder(deep_mode="none"),
    document_builder(deep_mode="moderate"),
    document_builder(deep_mode="extreme"),
    document_builder(deep_mode="ultra_deep"),
    st.just("")
)