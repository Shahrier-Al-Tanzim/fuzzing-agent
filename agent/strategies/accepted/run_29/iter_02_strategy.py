"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-08-21T09:28:15.494059+00:00
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
    kind = draw(st.sampled_from(["unquoted", "quoted", "dotted"]))
    if kind == "unquoted":
        base = draw(unquoted_key_strat)
        return f"{prefix}{base}" if prefix else base
    elif kind == "quoted":
        base = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10))
        return f'"{prefix}{base}"'
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
    st.sampled_from(["0x0", "0xDEADBEEF", "0x1234_5678", "0xfe"])
)

oct_int_strat = st.one_of(
    st.integers(min_value=0, max_value=0o7777).map(lambda x: f"0o{oct(x)[2:]}"),
    st.sampled_from(["0o0", "0o755", "0o0_7", "0o644"])
)

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
    frac = draw(st.sampled_from(["", ".123", ".9999999999999999999", ".000000001", ".5"]))
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

scalar_value = st.one_of(bool_strat, int_strat, float_strat, string_strat, datetime_strat())

@composite
def toml_value(draw, depth=0):
    if depth >= 8:
        return draw(scalar_value)
    
    kind = draw(st.sampled_from(["scalar", "array", "inline"]))
    if kind == "scalar":
        return draw(scalar_value)
    elif kind == "array":
        num_elems = draw(st.integers(0, 3))
        elems = [draw(toml_value(depth=depth + 1)) for _ in range(num_elems)]
        comma = draw(st.sampled_from([", ", "", ","])) if elems else ""
        return f"[{', '.join(elems)}{comma}]"
    else:
        num_pairs = draw(st.integers(0, 3))
        pairs = []
        for i in range(num_pairs):
            k = f"ik{i}_" + draw(unquoted_key_strat)
            v = draw(toml_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        trailing_comma = draw(st.sampled_from([", ", "", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing_comma}}}"

@composite
def deep_toml_value(draw):
    depth = draw(st.integers(100, 50000))
    kind = draw(st.sampled_from(["array", "inline", "mixed"]))
    val = draw(scalar_value)
    if kind == "array":
        return "[" * depth + val + "]" * depth
    elif kind == "inline":
        prefix = "".join(f"k{i} = {{" for i in range(depth))
        suffix = "}" * depth
        trailing = draw(st.sampled_from(["", ","]))
        return prefix + val + trailing + suffix
    else:
        prefix = "".join(f"[{{ k{i} = " for i in range(depth))
        suffix = "".join(" }]" for _ in range(depth))
        return prefix + val + suffix

@composite
def pair_strat(draw, prefix="", deep=False):
    k = draw(safe_key(prefix=prefix))
    v = draw(deep_toml_value()) if deep else draw(toml_value())
    eq = draw(st.sampled_from([" = ", "=", " = "]))
    return f"{k}{eq}{v}"

comment_strat = st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS, min_size=0, max_size=15).map(lambda s: f"# {s}")

@composite
def document_builder(draw, deep_bias=False):
    num_lines = draw(st.integers(1, 15))
    lines = []
    
    for idx in range(num_lines):
        line_type = draw(st.sampled_from([
            "pair", "pair", "pair", "pair", "table", "comment", "blank"
        ]))
        
        if line_type == "pair":
            prefix = f"k{idx}_"
            lines.append(draw(pair_strat(prefix=prefix, deep=deep_bias)))
        elif line_type == "table":
            prefix = f"t{idx}_"
            k = draw(safe_key(prefix=prefix))
            is_array_table = draw(st.booleans())
            if is_array_table:
                lines.append(f"[[{k}]]")
            else:
                lines.append(f"[{k}]")
        elif line_type == "comment":
            lines.append(draw(comment_strat))
        elif line_type == "blank":
            lines.append("")
            
    return "\n".join(lines)

toml_strategy = st.one_of(
    document_builder(deep_bias=False),
    document_builder(deep_bias=True),
    st.just("")
)